"""Complete training state, saved and restored across a process boundary.

The trunk-branch design in `drafts/v6-alt-wsd-design.md` runs one trunk and branches a decay
leg per budget rung. A leg must continue the trunk as if it had never stopped, so "training
state" here means everything the next step reads, not just the weights:

| | why it has to be here |
| --- | --- |
| model parameters | the obvious half |
| optimizer state — AdamW `m`, `v`, `step` | dropping `step` restarts the schedule and bias correction |
| `mx.random.state` | dropout and any sampling downstream of it |
| data-stream RNG | which windows the next batches are drawn from |
| deficit RNG | which permutation Deficit S draws, if the window is still open |

Leaving any one out produces a leg that trains fine and measures something else, which is the
failure mode this module exists to prevent. `tests/test_checkpoint.py` therefore checks each
component individually rather than only checking that a round trip works.

**Exact restoration is not the same as an exact trajectory.** MLX is not run-to-run
deterministic on this hardware — two runs of one config diverge — so a resumed run is not
bit-identical to an uninterrupted one, and neither is a repeat of the uninterrupted one.
`tools/branch_replay_check.py` measures both against the registered endpoint and against each
other; at the 4,320-step trunk the branch moves held-out loss by 1.9e-08 where mere repetition
moves it by 1.5e-08, both five orders under the baseline seed SD. What this module guarantees
is the part that *is* exact: the state written is the state read back.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import mlx.core as mx
import numpy as np
from mlx.utils import tree_flatten, tree_unflatten

# Bumped when the on-disk layout changes in a way older checkpoints cannot satisfy.
FORMAT_VERSION = 1

MODEL_PREFIX = "model."
OPTIMIZER_PREFIX = "opt."
MX_RANDOM_PREFIX = "mxrandom."


@dataclass(frozen=True)
class Streams:
    """The two numpy generators a run advances, kept together so neither is forgotten."""

    data: np.random.Generator
    deficit: np.random.Generator

    @classmethod
    def for_seed(cls, seed: int) -> "Streams":
        """The trainer's convention: the deficit stream is offset by one from the data stream."""
        return cls(np.random.default_rng(seed), np.random.default_rng(seed + 1))


def _subtree(arrays: dict, prefix: str):
    return tree_unflatten(
        [(k[len(prefix) :], v) for k, v in arrays.items() if k.startswith(prefix)]
    )


def save(path: Path, model, optimizer, streams: Streams, meta: dict | None = None) -> None:
    """Write complete training state to `path.npz` plus a `path.json` sidecar.

    The sidecar carries what is not an array: the numpy generator states, the format version,
    and whatever caller metadata identifies the branch point.
    """
    arrays = {f"{MODEL_PREFIX}{k}": v for k, v in tree_flatten(model.parameters())}
    arrays.update({f"{OPTIMIZER_PREFIX}{k}": v for k, v in tree_flatten(optimizer.state)})
    for index, part in enumerate(mx.random.state):
        arrays[f"{MX_RANDOM_PREFIX}{index}"] = part

    path.parent.mkdir(parents=True, exist_ok=True)
    mx.eval(list(arrays.values()))
    mx.savez(str(path.with_suffix(".npz")), **arrays)
    path.with_suffix(".json").write_text(
        json.dumps(
            {
                "format_version": FORMAT_VERSION,
                "data_rng": streams.data.bit_generator.state,
                "deficit_rng": streams.deficit.bit_generator.state,
                **(meta or {}),
            },
            indent=2,
        )
    )


def load_meta(path: Path) -> dict:
    payload = json.loads(path.with_suffix(".json").read_text())
    version = payload.get("format_version")
    if version != FORMAT_VERSION:
        raise ValueError(
            f"checkpoint {path} is format {version}, this build reads {FORMAT_VERSION}"
        )
    return payload


def restore(path: Path, model, optimizer, streams: Streams) -> Streams:
    """Load state into freshly constructed objects, in place.

    `model` and `optimizer` must already be built with the same architecture and optimizer
    class; this restores their contents, it does not construct them.
    """
    payload = load_meta(path)
    arrays = mx.load(str(path.with_suffix(".npz")))

    missing = [
        name
        for name, prefix in (
            ("model", MODEL_PREFIX),
            ("optimizer", OPTIMIZER_PREFIX),
            ("mx.random", MX_RANDOM_PREFIX),
        )
        if not any(k.startswith(prefix) for k in arrays)
    ]
    if missing:
        raise ValueError(f"checkpoint {path} is missing state for: {', '.join(missing)}")

    model.update(_subtree(arrays, MODEL_PREFIX))
    optimizer.state = _subtree(arrays, OPTIMIZER_PREFIX)
    mx.random.state = [
        arrays[f"{MX_RANDOM_PREFIX}{i}"] for i in range(len(mx.random.state))
    ]
    streams.data.bit_generator.state = payload["data_rng"]
    streams.deficit.bit_generator.state = payload["deficit_rng"]
    mx.eval(model.parameters(), optimizer.state)
    return streams

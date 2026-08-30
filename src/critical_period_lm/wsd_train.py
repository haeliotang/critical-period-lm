"""Trunk-branch trainer for the v6 draft: one trunk, one decay leg per budget rung.

**Draft infrastructure. Nothing here is registered**, and every record it writes lands under
`calibration/`. The v5 design is frozen and complete; a v6 freeze does not exist, so a
registered mode would have nothing to verify against. It is added when v6 is frozen, not
before — the trainer refusing to write registered records is the same gate `train.py` carries.

## What it does

    trunk   warmup -> constant peak rate, deficit applied at its window,
            run to (1 - decay_fraction) x largest rung,
            checkpointing complete state at each rung's branch point
    leg     restore a branch checkpoint, anneal to zero over that rung's decay,
            evaluate, write one record per rung

Two rungs therefore **share an identical trajectory** up to the shorter one's branch. "Same
deficit, more recovery" is a construction rather than an approximation, and the recovery
handicap that `analysis/handicap.py` had to verify empirically for v5 is true by construction.

## Why this is safe to do

Resuming from a checkpoint is not bit-identical to an uninterrupted run — but neither is a
repeat of the uninterrupted run, because MLX is not run-to-run deterministic on this hardware.
`tools/branch_replay_check.py` measures both against the registered endpoint at the 4,320-step
trunk: branching moves held-out loss by 1.9e-08 where repetition moves it by 1.5e-08, both five
orders of magnitude under the smallest baseline seed SD the study resolves. That check is a
standing gate, not a one-off — see `drafts/v6-alt-wsd-design.md` §8.

    python -m critical_period_lm.wsd_train --condition shuffle_600 \\
        --deficit shuffle --onset 600 --seed 18
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np

from . import wsd
from .checkpoint import Streams, restore, save
from .data import DATA_DIR, load_tokens
from .deficits import (
    FIXED,
    NONE,
    SHUFFLE,
    SHUFFLE_WINDOW,
    DeficitSchedule,
    make_window_permutation,
)
from .model import ModelConfig, Transformer
from .train import WINDOW_PERMUTATION_SEED, evaluate, evaluation_batches, training_batches

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "calibration" / "wsd"


def training_batches_from(tokens: np.ndarray, config: "WSDRunConfig", rng: np.random.Generator):
    """`train.training_batches`, with the stream's generator supplied so it can be saved.

    A leg must draw the batches the trunk would have drawn next, which means the generator has
    to survive the branch. `tests/test_wsd_train.py` pins this against the trainer's own
    iterator so the two cannot drift apart.
    """
    span = config.model.seq_len + 1
    high = tokens.size - span
    while True:
        offsets = rng.integers(0, high, size=config.batch_size)
        yield np.stack([tokens[o : o + span] for o in offsets]).astype(np.int32)


@dataclass
class WSDRunConfig:
    """One (condition, seed) trunk and the legs branched from it."""

    condition: str = "baseline"
    seed: int = 0
    deficit: str = NONE
    onset: int = 0
    duration: int = wsd.DEFICIT_STEPS
    rungs: tuple[int, ...] = wsd.RUNGS
    batch_size: int = 32
    learning_rate: float = 3e-4
    weight_decay: float = 0.1
    grad_clip: float = 1.0
    eval_batches: int = 32
    model: ModelConfig = field(default_factory=ModelConfig)

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["model"] = self.model.as_dict()
        payload["rungs"] = list(self.rungs)
        return payload

    def deficit_schedule(self) -> DeficitSchedule:
        """Absolute onset and duration — no clean-budget conversion.

        v5 expressed the window as a fraction of each rung's own budget so the rungs would be
        scale-invariant copies. Here the rungs share a trunk, so they are not copies of each
        other, they are the same run; an absolute onset strikes the same model state at the
        same learning rate for every rung, which is stronger than self-similarity.
        """
        if self.deficit == NONE:
            return DeficitSchedule()
        return DeficitSchedule(
            kind=self.deficit,
            onset_step=self.onset,
            duration_steps=self.duration,
            window_permutation=(
                make_window_permutation(WINDOW_PERMUTATION_SEED, SHUFFLE_WINDOW)
                if self.deficit == FIXED
                else None
            ),
        )

    @property
    def rate_matched(self) -> bool:
        return self.deficit == NONE or wsd.is_rate_matched(self.onset, self.duration, self.rungs)


def _build(config: WSDRunConfig, schedule):
    mx.random.seed(config.seed)
    model = Transformer(config.model)
    mx.eval(model.parameters())
    optimizer = optim.AdamW(learning_rate=schedule, weight_decay=config.weight_decay)
    return model, optimizer


def _compiled_step(config: WSDRunConfig, model, optimizer):
    def loss_fn(m, inputs, targets):
        return m.loss(inputs, targets)

    value_and_grad = nn.value_and_grad(model, loss_fn)
    state = [model.state, optimizer.state, mx.random.state]

    @partial(mx.compile, inputs=state, outputs=state)
    def step(inputs, targets):
        loss, grads = value_and_grad(model, inputs, targets)
        grads, _ = optim.clip_grad_norm(grads, config.grad_clip)
        optimizer.update(model, grads)
        return loss

    return step, state


def run_trunk(config: WSDRunConfig, data_dir: Path = DATA_DIR, out: Path = OUTPUT_DIR) -> dict:
    """Train the shared trunk, checkpointing complete state at every rung's branch point."""
    train_tokens, _ = load_tokens(data_dir)
    deficit = config.deficit_schedule()
    model, optimizer = _build(config, wsd.trunk_schedule(wsd.WSDConfig(peak=config.learning_rate)))
    streams = Streams.for_seed(config.seed)
    batches = training_batches_from(train_tokens, config, streams.data)
    step, state = _compiled_step(config, model, optimizer)

    branches = {wsd.branch_step(rung): rung for rung in config.rungs}
    stem = out / config.condition / f"seed{config.seed}"
    curve, deficit_steps, started = [], 0, time.time()

    for index in range(wsd.trunk_steps(config.rungs)):
        if index in branches:
            save(stem / f"branch-{branches[index]}", model, optimizer, streams,
                 {"trunk_step": index, "rung": branches[index]})
        batch = next(batches)
        if deficit.active_at(index):
            batch = deficit.apply(batch, index, streams.deficit)
            deficit_steps += 1
        tokens = mx.array(batch)
        loss = step(tokens[:, :-1], tokens[:, 1:])
        mx.eval(state)
        if index % 50 == 0:
            curve.append({"step": index, "loss": loss.item()})

    for branch_at, rung in branches.items():
        if branch_at >= wsd.trunk_steps(config.rungs):
            save(stem / f"branch-{rung}", model, optimizer, streams,
                 {"trunk_step": branch_at, "rung": rung})

    return {
        "trunk_steps": wsd.trunk_steps(config.rungs),
        "deficit_steps": deficit_steps,
        "train_curve": curve,
        "wall_clock_seconds": time.time() - started,
    }


def run_leg(config: WSDRunConfig, rung: int, data_dir: Path = DATA_DIR,
            out: Path = OUTPUT_DIR) -> dict:
    """Anneal one rung's decay leg from its branch checkpoint and measure it."""
    train_tokens, valid_tokens = load_tokens(data_dir)
    deficit = config.deficit_schedule()
    model, optimizer = _build(config, wsd.leg_schedule(rung, wsd.WSDConfig(peak=config.learning_rate)))
    streams = Streams.for_seed(config.seed)

    stem = out / config.condition / f"seed{config.seed}"
    restore(stem / f"branch-{rung}", model, optimizer, streams)
    branch_at = wsd.branch_step(rung)

    batches = training_batches_from(train_tokens, config, streams.data)
    step, state = _compiled_step(config, model, optimizer)
    started = time.time()

    for offset in range(wsd.leg_steps(rung)):
        batch = next(batches)
        # The deficit window lives in the trunk by construction, but a leg is still asked
        # rather than assumed: an onset late enough to reach into a leg would otherwise be
        # silently dropped.
        absolute = branch_at + offset
        if deficit.active_at(absolute):
            batch = deficit.apply(batch, absolute, streams.deficit)
        tokens = mx.array(batch)
        step(tokens[:, :-1], tokens[:, 1:])
        mx.eval(state)

    final = evaluate(model, evaluation_batches(valid_tokens, config))
    record = {
        "condition": config.condition,
        "seed": config.seed,
        "total_steps": rung,
        "final_eval_loss": final,
        "branch_step": branch_at,
        "leg_steps": wsd.leg_steps(rung),
        "rate_matched": config.rate_matched,
        "config": config.as_dict(),
        "wall_clock_seconds": time.time() - started,
        "registered": False,
    }
    destination = stem / f"rung-{rung}.json"
    destination.write_text(json.dumps(record, indent=2))
    return record


def run(config: WSDRunConfig, data_dir: Path = DATA_DIR, out: Path = OUTPUT_DIR) -> list[dict]:
    trunk = run_trunk(config, data_dir, out)
    print(f"trunk {trunk['trunk_steps']} steps, {trunk['deficit_steps']} under deficit, "
          f"{trunk['wall_clock_seconds']:.0f}s")
    records = []
    for rung in sorted(config.rungs):
        record = run_leg(config, rung, data_dir, out)
        records.append(record)
        print(f"  rung {rung:>6}: eval {record['final_eval_loss']:.4f} "
              f"({record['wall_clock_seconds']:.0f}s)")
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", default="baseline")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--deficit", choices=[NONE, SHUFFLE, FIXED], default=NONE)
    parser.add_argument("--onset", type=int, default=0)
    parser.add_argument("--duration", type=int, default=wsd.DEFICIT_STEPS)
    args = parser.parse_args()

    config = WSDRunConfig(
        condition=args.condition, seed=args.seed, deficit=args.deficit,
        onset=args.onset, duration=args.duration,
    )
    if config.deficit != NONE and not config.rate_matched:
        print(f"note: onset {config.onset} is not learning-rate-matched "
              f"(stable phase is {wsd.stable_phase(config.rungs)}); "
              "it may not carry the primary contrast", file=sys.stderr)
    run(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

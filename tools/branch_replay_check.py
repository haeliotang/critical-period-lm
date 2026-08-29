"""Does resuming from a checkpoint perturb the endpoint more than running twice does?

This decides between the two v6 drafts and nothing else. It is not analysis, produces no
result, and touches no registered record.

`drafts/v6-alt-wsd-design.md` proposes one trunk with a decay leg branched per rung, which
makes "same deficit, more recovery" a construction rather than an approximation and costs 34%
less than separate runs. It rests on one unverified assumption: that training state can cross
a process boundary without moving the measurement.

**The obvious test is the wrong one.** Asking whether a resumed run reproduces an
uninterrupted one *bit for bit* presumes the platform is deterministic, and it is not: two
runs of the identical config in separate processes diverge here at around step 28 and end with
different weights. Bit-exactness is unavailable to a run compared against itself, so demanding
it of a branch measures the platform, not the design.

The right question is comparative, and needs a control:

    straight-a   N steps                          }  their difference is the noise floor
    straight-b   N steps, same config, again      }
    first        K steps, checkpoint
    resume       load it, run the remaining N-K   -> compare against that floor

**A branch is acceptable when it moves the registered endpoint --- held-out loss --- by no
more than two runs of the same config move it, and when both are far below the baseline seed
scatter the study actually resolves.** That last clause is what makes the criterion meaningful
rather than merely relative: a floor is only reassuring if it sits well under the smallest
real effect.

Four phases, four processes, on purpose. Rebuilding objects inside one process leaves MLX's
compilation cache and global RNG warm, which is where a defect would hide.

    python tools/branch_replay_check.py                          # 150 steps, branch at 100
    python tools/branch_replay_check.py --steps 600 --branch-at 400

Exit status is 0 only if the branch stays inside the tolerance.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import mlx.core as mx  # noqa: E402
import mlx.nn as nn  # noqa: E402
import mlx.optimizers as optim  # noqa: E402
import numpy as np  # noqa: E402
from mlx.utils import tree_flatten, tree_unflatten  # noqa: E402

from critical_period_lm.data import load_tokens  # noqa: E402
from critical_period_lm.model import Transformer  # noqa: E402
from critical_period_lm.train import (  # noqa: E402
    TrainConfig,
    build_schedule,
    evaluate,
    evaluation_batches,
    training_batches,
)

SCRATCH = ROOT / "tmp" / "branch-replay"

# The smallest baseline seed SD across v5's rungs, in nats. The branch must be far under it,
# not merely under the noise floor of repeated runs.
SMALLEST_SEED_SD = 0.00235
TOLERANCE = 0.1 * SMALLEST_SEED_SD


def batches_from(tokens: np.ndarray, config: TrainConfig, rng: np.random.Generator):
    """`train.training_batches`, with the generator handed in so it can be saved.

    `assert_matches_trainer` checks this against the trainer's own iterator, so the file
    cannot drift into testing something else.
    """
    span = config.model.seq_len + 1
    high = tokens.size - span
    while True:
        offsets = rng.integers(0, high, size=config.batch_size)
        yield np.stack([tokens[o : o + span] for o in offsets]).astype(np.int32)


def assert_matches_trainer(tokens: np.ndarray, config: TrainConfig) -> None:
    mine = batches_from(tokens, config, np.random.default_rng(config.seed))
    theirs = training_batches(tokens, config)
    for _ in range(3):
        if not np.array_equal(next(mine), next(theirs)):
            raise SystemExit("local batch iterator diverges from train.training_batches")


def capture(model, optimizer, data_rng, deficit_rng):
    arrays = {f"model.{k}": v for k, v in tree_flatten(model.parameters())}
    arrays.update({f"opt.{k}": v for k, v in tree_flatten(optimizer.state)})
    for i, part in enumerate(mx.random.state):
        arrays[f"mxrandom.{i}"] = part
    meta = {
        "data_rng": data_rng.bit_generator.state,
        "deficit_rng": deficit_rng.bit_generator.state,
    }
    return arrays, meta


def save(path: Path, model, optimizer, data_rng, deficit_rng) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays, meta = capture(model, optimizer, data_rng, deficit_rng)
    mx.eval(list(arrays.values()))
    mx.savez(str(path.with_suffix(".npz")), **arrays)
    path.with_suffix(".json").write_text(json.dumps(meta))


def restore(path: Path, model, optimizer, data_rng, deficit_rng):
    arrays = mx.load(str(path.with_suffix(".npz")))
    meta = json.loads(path.with_suffix(".json").read_text())

    def subtree(prefix):
        return tree_unflatten(
            [(k[len(prefix) :], v) for k, v in arrays.items() if k.startswith(prefix)]
        )

    model.update(subtree("model."))
    optimizer.state = subtree("opt.")
    mx.random.state = [arrays[f"mxrandom.{i}"] for i in range(len(mx.random.state))]
    data_rng.bit_generator.state = meta["data_rng"]
    deficit_rng.bit_generator.state = meta["deficit_rng"]
    mx.eval(model.parameters(), optimizer.state)
    return model, optimizer, data_rng, deficit_rng


def run(config: TrainConfig, steps: int, resume_from: Path | None, save_to: Path) -> float:
    """Mirrors the trainer's loop, including the compiled step over a captured state list."""
    train_tokens, valid_tokens = load_tokens(ROOT / "data")
    assert_matches_trainer(train_tokens, config)

    mx.random.seed(config.seed)
    model = Transformer(config.model)
    mx.eval(model.parameters())
    optimizer = optim.AdamW(
        learning_rate=build_schedule(config), weight_decay=config.weight_decay
    )
    data_rng = np.random.default_rng(config.seed)
    deficit_rng = np.random.default_rng(config.seed + 1)
    if resume_from is not None:
        model, optimizer, data_rng, deficit_rng = restore(
            resume_from, model, optimizer, data_rng, deficit_rng
        )

    batches = batches_from(train_tokens, config, data_rng)

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

    for _ in range(steps):
        batch = mx.array(next(batches))
        step(batch[:, :-1], batch[:, 1:])
        mx.eval(state)

    save(save_to, model, optimizer, data_rng, deficit_rng)
    return evaluate(model, evaluation_batches(valid_tokens, config))


def weight_gap(left: Path, right: Path) -> float:
    a, b = mx.load(str(left.with_suffix(".npz"))), mx.load(str(right.with_suffix(".npz")))
    worst = 0.0
    for key in a:
        if a[key].dtype in (mx.uint32, mx.uint64):
            continue
        worst = max(
            worst, mx.max(mx.abs(a[key].astype(mx.float32) - b[key].astype(mx.float32))).item()
        )
    return worst


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase", choices=["straight-a", "straight-b", "first", "resume"], default=None
    )
    parser.add_argument("--steps", type=int, default=150)
    parser.add_argument("--branch-at", type=int, default=100)
    # Seed 99 is outside every calibration and registered set, so nothing here can collide
    # with, or be mistaken for, a run that means something.
    parser.add_argument("--seed", type=int, default=99)
    args = parser.parse_args()

    if args.branch_at >= args.steps:
        raise SystemExit("--branch-at must be less than --steps")

    config = TrainConfig(total_steps=args.steps, seed=args.seed)
    SCRATCH.mkdir(parents=True, exist_ok=True)
    phases = {
        "straight-a": (args.steps, None, "straight-a"),
        "straight-b": (args.steps, None, "straight-b"),
        "first": (args.branch_at, None, "checkpoint"),
        "resume": (args.steps - args.branch_at, SCRATCH / "checkpoint", "resumed"),
    }

    if args.phase:
        steps, resume_from, name = phases[args.phase]
        loss = run(config, steps, resume_from, SCRATCH / name)
        (SCRATCH / f"{name}-eval.json").write_text(json.dumps(loss))
        return 0

    for phase in phases:
        print(f"--- {phase} " + "-" * 44)
        done = subprocess.run(
            [sys.executable, __file__, "--phase", phase, "--steps", str(args.steps),
             "--branch-at", str(args.branch_at), "--seed", str(args.seed)], cwd=ROOT,
        )
        if done.returncode != 0:
            return done.returncode

    loss = {n: json.loads((SCRATCH / f"{n}-eval.json").read_text())
            for n in ("straight-a", "straight-b", "resumed")}
    floor = abs(loss["straight-a"] - loss["straight-b"])
    branch = abs(loss["straight-b"] - loss["resumed"])

    print(f"\n{args.steps} steps, branched at {args.branch_at}, seed {args.seed}\n")
    for name, value in loss.items():
        print(f"  {name:<12} held-out loss {value:.10f}")
    print(f"\n  noise floor  |straight-a - straight-b| = {floor:.3e}")
    print(f"  branch cost  |straight-b - resumed|     = {branch:.3e}")
    print(f"  weights: floor {weight_gap(SCRATCH/'straight-a', SCRATCH/'straight-b'):.3e}, "
          f"branch {weight_gap(SCRATCH/'straight-b', SCRATCH/'resumed'):.3e}")
    print(f"\n  tolerance {TOLERANCE:.3e}  (a tenth of the smallest baseline seed SD, "
          f"{SMALLEST_SEED_SD})")

    if branch > TOLERANCE:
        print("\nFAIL  branching moves the endpoint by a non-trivial fraction of the seed")
        print("scatter. The trunk-branch design in drafts/v6-alt-wsd-design.md is not")
        print("safe to build; take the cosine sweep in drafts/v6-onset-sweep-design.md.")
        return 1

    print(f"\nPASS  branching perturbs the endpoint {branch/SMALLEST_SEED_SD:.1e} of a seed SD,")
    print(f"      against a floor of {floor/SMALLEST_SEED_SD:.1e} for merely running twice.")
    print("\nWhat this does NOT establish: that the margin holds at the full trunk length")
    print("(divergence compounds with horizon -- rerun with --steps near the real trunk),")
    print("across MLX versions, or on another machine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

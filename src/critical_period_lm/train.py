"""Trainer for one run of the grid.

Not part of the freeze corpus. What it must guarantee is that a run record is a faithful,
immutable account of what happened: the config hash, the seed, the deficit schedule that
was actually honoured, the loss curves, and the total step count that the decision code
checks for equality across the grid.

Two mechanical gates live here rather than in a person's memory:

- a registered run refuses to start unless the design is frozen and the freeze verifies;
- a run refuses to overwrite an existing record, because a re-run of an identical config
  is a collision to notice, not a file to replace.

Calibration is exploratory, is written outside `runs/`, and is exempt from the first gate.

Usage:

    python -m critical_period_lm.train --calibration --total-steps 200
    python -m critical_period_lm.train --condition shuffle_early_N4 --seed 0 \
        --deficit shuffle --onset-frac 0.0 --duration-frac 0.16 --total-steps 43200
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from functools import partial
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np

from critical_period_lm import freeze
from critical_period_lm.data import DATA_DIR, load_tokens
from critical_period_lm.deficits import NONE, PERMUTE, DeficitSchedule, make_vocab_permutation
from critical_period_lm.model import ModelConfig, Transformer

ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT / "runs"
CALIBRATION_DIR = ROOT / "calibration"

# Fixed for the whole study so that Deficit P is the same relabeling in every run.
VOCAB_PERMUTATION_SEED = 20260806


@dataclass(frozen=True)
class TrainConfig:
    condition: str = "baseline"
    seed: int = 0
    deficit: str = NONE
    onset_frac: float = 0.0
    duration_frac: float = 0.0
    total_steps: int = 43_200
    batch_size: int = 32
    learning_rate: float = 3e-4
    warmup_steps: int = 500
    weight_decay: float = 0.1
    grad_clip: float = 1.0
    eval_every: int = 500
    eval_batches: int = 32
    model: ModelConfig = field(default_factory=ModelConfig)

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["model"] = self.model.as_dict()
        return payload

    def config_hash(self, data_manifest: dict) -> str:
        payload = {"train": self.as_dict(), "data": data_manifest}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(canonical).hexdigest()[:16]

    def schedule(self) -> DeficitSchedule:
        """Deficit onset and duration are fractions of total steps, resolved once here."""
        if self.deficit == NONE:
            return DeficitSchedule()
        permutation = (
            make_vocab_permutation(self.model.vocab_size, VOCAB_PERMUTATION_SEED)
            if self.deficit == PERMUTE
            else None
        )
        return DeficitSchedule(
            kind=self.deficit,
            onset_step=round(self.onset_frac * self.total_steps),
            duration_steps=round(self.duration_frac * self.total_steps),
            vocab_permutation=permutation,
        )


def training_batches(tokens: np.ndarray, config: TrainConfig):
    """Yield `(batch, seq_len + 1)` windows.

    The stream is seeded by `seed` alone and not by the condition, so two runs with the
    same seed see the same data in the same order and differ only in the deficit. That is
    what makes the seed a paired unit rather than a second source of noise.
    """
    rng = np.random.default_rng(config.seed)
    span = config.model.seq_len + 1
    high = tokens.size - span
    while True:
        offsets = rng.integers(0, high, size=config.batch_size)
        yield np.stack([tokens[o : o + span] for o in offsets]).astype(np.int32)


def evaluation_batches(tokens: np.ndarray, config: TrainConfig) -> np.ndarray:
    """Fixed, contiguous, non-overlapping validation windows. Identical for every run."""
    span = config.model.seq_len + 1
    needed = config.eval_batches * config.batch_size
    windows = np.stack([tokens[i * span : (i + 1) * span] for i in range(needed)])
    return windows.astype(np.int32).reshape(config.eval_batches, config.batch_size, span)


def evaluate(model: Transformer, batches: np.ndarray) -> float:
    model.eval()
    total = 0.0
    for batch in batches:
        tokens = mx.array(batch)
        total += model.loss(tokens[:, :-1], tokens[:, 1:]).item()
    model.train()
    return total / len(batches)


def build_schedule(config: TrainConfig):
    warmup = optim.linear_schedule(0.0, config.learning_rate, config.warmup_steps)
    decay = optim.cosine_decay(
        config.learning_rate,
        max(config.total_steps - config.warmup_steps, 1),
        config.learning_rate * 0.1,
    )
    return optim.join_schedules([warmup, decay], [config.warmup_steps])


def train(config: TrainConfig, data_dir: Path = DATA_DIR, calibration: bool = False) -> dict:
    data_manifest = json.loads((data_dir / "manifest.json").read_text())
    config_hash = config.config_hash(data_manifest)

    destination = (CALIBRATION_DIR if calibration else RUNS_DIR) / config_hash
    if (destination / "run.json").exists():
        raise FileExistsError(
            f"a record for config {config_hash} already exists at {destination}. "
            "An identical configuration was already run; that is a collision to explain, "
            "not a file to overwrite."
        )

    if not calibration:
        problems = freeze.verify_manifest()
        if problems:
            raise RuntimeError(
                "registered runs require an intact freeze; "
                + "; ".join(problems)
                + ". Use --calibration for exploratory runs."
            )

    train_tokens, valid_tokens = load_tokens(data_dir)
    schedule = config.schedule()

    mx.random.seed(config.seed)
    model = Transformer(config.model)
    mx.eval(model.parameters())
    optimizer = optim.AdamW(
        learning_rate=build_schedule(config), weight_decay=config.weight_decay
    )

    def loss_fn(m: Transformer, inputs: mx.array, targets: mx.array) -> mx.array:
        return m.loss(inputs, targets)

    value_and_grad = nn.value_and_grad(model, loss_fn)
    state = [model.state, optimizer.state, mx.random.state]

    @partial(mx.compile, inputs=state, outputs=state)
    def step(inputs: mx.array, targets: mx.array) -> mx.array:
        loss, grads = value_and_grad(model, inputs, targets)
        grads, _ = optim.clip_grad_norm(grads, config.grad_clip)
        optimizer.update(model, grads)
        return loss

    eval_windows = evaluation_batches(valid_tokens, config)
    batches = training_batches(train_tokens, config)
    deficit_rng = np.random.default_rng(config.seed + 1)

    train_curve: list[dict] = []
    eval_curve: list[dict] = []
    deficit_steps = 0
    started = time.time()

    for step_index in range(config.total_steps):
        batch = next(batches)
        if schedule.active_at(step_index):
            batch = schedule.apply(batch, step_index, deficit_rng)
            deficit_steps += 1

        tokens = mx.array(batch)
        loss = step(tokens[:, :-1], tokens[:, 1:])
        mx.eval(state)

        if step_index % 50 == 0:
            train_curve.append({"step": step_index, "loss": loss.item()})
        if step_index % config.eval_every == 0:
            eval_loss = evaluate(model, eval_windows)
            eval_curve.append({"step": step_index, "loss": eval_loss})
            elapsed = time.time() - started
            print(
                f"step {step_index:>6}/{config.total_steps} "
                f"train {loss.item():.4f} eval {eval_loss:.4f} "
                f"{'deficit' if schedule.active_at(step_index) else 'clean':>7} "
                f"{elapsed:.0f}s"
            )

    final_eval_loss = evaluate(model, eval_windows)
    elapsed = time.time() - started
    tokens_seen = config.total_steps * config.batch_size * config.model.seq_len

    record = {
        "config_hash": config_hash,
        "condition": config.condition,
        "seed": config.seed,
        "calibration": calibration,
        "total_steps": config.total_steps,
        "final_eval_loss": final_eval_loss,
        "deficit": {
            "kind": schedule.kind,
            "onset_step": schedule.onset_step,
            "duration_steps": schedule.duration_steps,
            "steps_actually_applied": deficit_steps,
        },
        "config": config.as_dict(),
        "data_manifest": data_manifest,
        "model": {
            "n_params": model.n_params,
            "n_params_non_embedding": model.n_params_non_embedding,
        },
        "throughput": {
            "wall_clock_seconds": elapsed,
            "tokens_seen": tokens_seen,
            "tokens_per_second": tokens_seen / elapsed,
        },
        "train_curve": train_curve,
        "eval_curve": eval_curve + [{"step": config.total_steps, "loss": final_eval_loss}],
    }

    destination.mkdir(parents=True, exist_ok=True)
    incomplete = destination / "run.json.partial"
    incomplete.write_text(json.dumps(record, indent=2) + "\n")
    incomplete.rename(destination / "run.json")

    print(
        f"\n{config.condition} seed {config.seed}: final eval loss "
        f"{final_eval_loss:.4f} nats/token, {deficit_steps} deficit steps, "
        f"{elapsed / 60:.1f} min, {tokens_seen / elapsed / 1000:.1f}k tok/s"
    )
    print(f"record: {destination / 'run.json'}")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition", default="baseline")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--deficit", choices=["none", "shuffle", "permute"], default="none")
    parser.add_argument("--onset-frac", type=float, default=0.0)
    parser.add_argument("--duration-frac", type=float, default=0.0)
    parser.add_argument("--total-steps", type=int, default=TrainConfig.total_steps)
    parser.add_argument("--batch-size", type=int, default=TrainConfig.batch_size)
    parser.add_argument("--seq-len", type=int, default=ModelConfig.seq_len)
    parser.add_argument("--n-layers", type=int, default=ModelConfig.n_layers)
    parser.add_argument("--d-model", type=int, default=ModelConfig.d_model)
    parser.add_argument("--eval-every", type=int, default=TrainConfig.eval_every)
    parser.add_argument("--eval-batches", type=int, default=TrainConfig.eval_batches)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument(
        "--calibration",
        action="store_true",
        help="exploratory run: written outside runs/, exempt from the freeze gate",
    )
    args = parser.parse_args()

    data_manifest = json.loads((args.data_dir / "manifest.json").read_text())
    model = ModelConfig(
        vocab_size=data_manifest["vocab_size"],
        d_model=args.d_model,
        n_layers=args.n_layers,
        seq_len=args.seq_len,
    )
    config = TrainConfig(
        condition=args.condition,
        seed=args.seed,
        deficit=args.deficit,
        onset_frac=args.onset_frac,
        duration_frac=args.duration_frac,
        total_steps=args.total_steps,
        batch_size=args.batch_size,
        eval_every=args.eval_every,
        eval_batches=args.eval_batches,
        model=model,
    )
    train(config, args.data_dir, calibration=args.calibration)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

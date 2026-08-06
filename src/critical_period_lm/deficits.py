"""The two registered training deficits and their schedule.

Part of the freeze corpus. These functions define the experimental manipulation, so a
change here after freeze is a change to the design, not to the implementation.

Both deficits operate on batches of token ids shaped `(batch, seq)` and are applied to the
training stream before input and target are split, so a corrupted batch is corrupted
consistently on both sides. Evaluation batches never pass through here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

NONE = "none"
SHUFFLE = "shuffle"
PERMUTE = "permute"

# Registered window size for Deficit S, in tokens.
SHUFFLE_WINDOW = 16

# --- Registered budget geometry, Sections 4.3 and 4.4 -------------------------------
#
# Deficit onsets and durations are fractions of the CLEAN budget T, not of the total run
# length. Every run is `T_total = N4 + R*T = 2.16*T` steps long, so a fraction of T is a
# 2.16-times-smaller fraction of the run. Getting this denominator wrong shrinks the
# recovery allowance and inflates the asymmetry between the early and late arms, which is
# exactly what happened in pilot 1: the deficit ran at 16% of training instead of 7.4%, and
# the late arm was left with 2.5 times less post-deficit training than the early arm
# instead of 1.33 times less.
#
# These constants live in the freeze corpus and are applied by `steps_from_clean_budget`.
# They are not to be re-derived at a call site.

RECOVERY_MULTIPLIER = 2.0
DEFICIT_FRACTIONS = (0.02, 0.04, 0.08, 0.16)
LATE_ONSET_FRACTION = 0.5
TOTAL_BUDGET_MULTIPLE = max(DEFICIT_FRACTIONS) + RECOVERY_MULTIPLIER  # 2.16


def clean_budget(total_steps: int) -> float:
    """Recover `T` from a run's total length. The inverse of `T_total = 2.16*T`."""
    return total_steps / TOTAL_BUDGET_MULTIPLE


def steps_from_clean_budget(total_steps: int, fraction: float) -> int:
    """Convert a registered fraction of `T` into optimizer steps."""
    return round(fraction * clean_budget(total_steps))


def window_shuffle(
    tokens: np.ndarray, rng: np.random.Generator, window: int = SHUFFLE_WINDOW
) -> np.ndarray:
    """Deficit S: permute token order within non-overlapping windows.

    Destroys local sequential structure while leaving the token-frequency distribution of
    every sequence exactly intact — the sequence is a permutation of itself. A trailing
    span shorter than `window` is shuffled within itself rather than left clean, so no
    position in the batch escapes the deficit.

    Permutations are resampled for every window of every sequence on every call, so the
    model cannot learn a fixed reordering.
    """
    if window < 2:
        raise ValueError("shuffle window must be at least 2 tokens")

    out = np.empty_like(tokens)
    seq_len = tokens.shape[-1]
    for start in range(0, seq_len, window):
        stop = min(start + window, seq_len)
        span = tokens[..., start:stop]
        if stop - start < 2:
            out[..., start:stop] = span
            continue
        order = np.argsort(rng.random(span.shape), axis=-1)
        out[..., start:stop] = np.take_along_axis(span, order, axis=-1)
    return out


def make_vocab_permutation(vocab_size: int, seed: int) -> np.ndarray:
    """The fixed bijection used by Deficit P. One per study, not one per batch."""
    return np.random.default_rng(seed).permutation(vocab_size)


def apply_vocab_permutation(tokens: np.ndarray, permutation: np.ndarray) -> np.ndarray:
    """Deficit P: relabel every token id through a fixed bijection.

    The corrupted task is isomorphic to the clean task. Every statistical regularity of the
    corpus survives, relabeled, so a model trained under this deficit learns a sound model
    of a renamed language. On removal it must remap its embedding and output layers while
    its interior structure remains applicable.
    """
    return permutation[tokens]


@dataclass(frozen=True)
class DeficitSchedule:
    """When a deficit is active, in optimizer steps.

    The window is half-open: `[onset_step, onset_step + duration_steps)`. A schedule with
    kind NONE is the baseline and is never active.
    """

    kind: str = NONE
    onset_step: int = 0
    duration_steps: int = 0
    vocab_permutation: np.ndarray | None = None

    def __post_init__(self) -> None:
        if self.kind not in (NONE, SHUFFLE, PERMUTE):
            raise ValueError(f"unknown deficit kind: {self.kind}")
        if self.onset_step < 0 or self.duration_steps < 0:
            raise ValueError("schedule bounds must be non-negative")
        if self.kind == PERMUTE and self.vocab_permutation is None:
            raise ValueError("Deficit P requires a fixed vocabulary permutation")

    def active_at(self, step: int) -> bool:
        if self.kind == NONE or self.duration_steps == 0:
            return False
        return self.onset_step <= step < self.onset_step + self.duration_steps

    def apply(self, tokens: np.ndarray, step: int, rng: np.random.Generator) -> np.ndarray:
        if not self.active_at(step):
            return tokens
        if self.kind == SHUFFLE:
            return window_shuffle(tokens, rng)
        return apply_vocab_permutation(tokens, self.vocab_permutation)

"""Warmup–stable–decay schedule and trunk/leg geometry for the v6 design.

Draft geometry for `drafts/v6-alt-wsd-design.md`. **Nothing here is registered.** These are
the numbers a preregistration would freeze, kept in code so the design can be exercised and
tested before it is written down as prose.

## What the stable phase buys

Under v5's cosine-over-the-whole-budget, moving a deficit later in training also moves it to a
lower learning rate. "When in training" and "at what learning rate" are one axis, and every
onset result this project has produced is a statement about that single confounded axis.

A stable phase holds the learning rate at its peak, so two deficits placed at different steps
inside it differ in **training time only**. That is the entire point of the schedule; the
warmup and decay legs exist to make the runs start and finish comparably.

## Why the geometry is absolute, not fractional

v5 made every quantity a fraction of the rung's own budget so the rungs would be
scale-invariant copies of each other. This design does not need self-similarity — it needs
*identical treatment*, which is stronger and which the shared trunk supplies directly. The
deficit therefore strikes at the same absolute step, at the same learning rate, against the
same model state, at every rung, because up to the branch point every rung **is** the same run.

Fractional warmup was v5's fix for a real defect (pilot 2's fixed 500-step warmup covered the
whole deficit at small scale and a sixth of it at large). That defect cannot recur here: there
is one warmup, in one trunk, shared by every rung.
"""

from __future__ import annotations

from dataclasses import dataclass

import mlx.optimizers as optim

# --- Draft geometry. Not registered. --------------------------------------------------

#: Budget rungs, in optimizer steps. The legs anneal from a shared trunk to these lengths.
RUNGS = (1_350, 2_700, 5_400)

#: Fraction of each rung spent annealing to zero. The trunk runs to `(1 - DECAY_FRACTION)`
#: of the largest rung, and each leg is its own rung's decay.
DECAY_FRACTION = 0.2

#: Absolute warmup, shared by every rung because there is only one trunk.
WARMUP_STEPS = 108

#: Deficit length in steps, absolute and identical at every onset and rung.
DEFICIT_STEPS = 400

#: Candidate onsets in steps. `0` is deliberately included and deliberately marked: it is the
#: only onset overlapping warmup, so it is the one onset *not* learning-rate-matched to the
#: others and may not carry the primary contrast. See the draft, §5.1.
ONSETS = (0, WARMUP_STEPS, 600, 1_400, 2_600, 3_800)
UNMATCHED_ONSETS = (0,)


def trunk_steps(rungs: tuple[int, ...] = RUNGS) -> int:
    """Length of the shared trunk: up to the largest rung's decay point."""
    return branch_step(max(rungs))


def branch_step(rung: int) -> int:
    """Step at which `rung`'s decay leg leaves the trunk."""
    return round((1.0 - DECAY_FRACTION) * rung)


def leg_steps(rung: int) -> int:
    """Length of `rung`'s decay leg."""
    return rung - branch_step(rung)


def total_steps(rungs: tuple[int, ...] = RUNGS) -> int:
    """Steps actually run per (condition, seed) — the saving over separate runs."""
    return trunk_steps(rungs) + sum(leg_steps(r) for r in rungs)


def separate_steps(rungs: tuple[int, ...] = RUNGS) -> int:
    """Steps the same ladder would cost as independent runs."""
    return sum(rungs)


def stable_phase(rungs: tuple[int, ...] = RUNGS) -> tuple[int, int]:
    """Half-open step range over which the learning rate is constant at its peak."""
    return WARMUP_STEPS, trunk_steps(rungs)


def is_rate_matched(onset: int, duration: int = DEFICIT_STEPS,
                    rungs: tuple[int, ...] = RUNGS) -> bool:
    """Does a deficit at `onset` lie wholly inside the constant-rate phase?

    Onsets that fail this are not comparable to those that pass on the design's own terms,
    because their deficit spans a changing learning rate.
    """
    start, stop = stable_phase(rungs)
    return start <= onset and onset + duration <= stop


@dataclass(frozen=True)
class WSDConfig:
    """The schedule's shape. Peak rate and rung come from the run being built."""

    peak: float = 3e-4
    warmup: int = WARMUP_STEPS
    decay_fraction: float = DECAY_FRACTION


def trunk_schedule(config: WSDConfig = WSDConfig()):
    """Warmup, then constant peak. The trunk never decays; its legs do.

    MLX has no constant schedule, so the stable phase is a linear schedule from the peak to
    itself. That is a constant, not an approximation of one.
    """
    warmup = optim.linear_schedule(0.0, config.peak, config.warmup)
    stable = optim.linear_schedule(config.peak, config.peak, 1)
    return optim.join_schedules([warmup, stable], [config.warmup])


def leg_schedule(rung: int, config: WSDConfig = WSDConfig()):
    """Cosine from peak to exactly zero over this rung's decay.

    Zero rather than a fraction of peak, for the reason v5 registered and verified: under a
    schedule leaving a non-trivial rate at the end the loss never stops falling, so an arm
    with less post-deficit training carries a permanent handicap that imitates the effect.
    The step counter restarts at the branch, so the leg's schedule is indexed from 0.
    """
    return optim.cosine_decay(config.peak, max(leg_steps(rung), 1), 0.0)

"""Frozen decision rules for the critical-period study.

This module is part of the freeze corpus. Once `freeze-manifest.json` is tagged, any
change here invalidates the freeze and requires a new design version.

Everything here is a pure function over run records. Nothing reads the filesystem, nothing
touches a model, and nothing is random: the tests are exact enumerations, so a verdict is
reproducible from the records alone.

## The endpoint is a decay, not a level

Design versions up to v1.3 scored damage as the loss difference at the end of one training
budget. The budget-doubling diagnostic showed that endpoint cannot do its job: at 5,400
steps the late-arm gap was 0.0370 and at 10,800 it was 0.0213, a fall of 42% on a single
doubling. A difference that shrinks when you train longer is unrepaired damage, not
permanent damage, and annealing the learning rate to zero merely freezes it in place at
whatever budget the run happened to stop at.

So the registered question — can later training repair the damage — is asked directly:
**does the gap to baseline go to zero as the training budget grows?** Each condition is run
at a ladder of budgets, the gap is paired against the baseline seed by seed, and the
registered statistic is the slope of that gap against log budget.

Sample sizes are 3 to 5 runs per cell, so normal-theory tests are not defensible and every
comparison here is an exact permutation test. Two different exchangeability arguments are
used, and they are not interchangeable:

- comparing two conditions at one budget permutes the condition labels;
- testing decay across budgets permutes the budget labels over the observed gaps. A paired
  sign-flip test was considered and rejected: at three seeds it enumerates 2^3 = 8 sign
  assignments, so its smallest attainable p-value is 0.125 and it can never reject at 0.05.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from statistics import fmean, stdev

# --- Registered constants. Frozen. -------------------------------------------------

ALPHA = 0.05
MARGIN_SD_MULTIPLE = 3.0
MARGIN_FLOOR_NATS = 0.01

BASELINE = "baseline"
PRIMARY_EARLY = "shuffle_early_N4"
PRIMARY_LATE = "shuffle_late_N4"
NEGATIVE_CONTROL_PREFIX = "fixed_early_"

# Enumerating budget-label assignments is exact up to this many; beyond it the enumeration
# is truncated deterministically rather than sampled, so a verdict never depends on a draw.
MAX_ENUMERATED_ASSIGNMENTS = 200_000

# Per-condition ladder verdicts.
TRANSIENT = "TRANSIENT"
PERSISTENT = "PERSISTENT"
DECAYING_UNRESOLVED = "DECAYING_UNRESOLVED"
NO_EFFECT = "NO_EFFECT"
UNDETERMINED = "UNDETERMINED"

# Study verdicts.
CRITICAL_PERIOD = "CRITICAL_PERIOD"
NO_CRITICAL_PERIOD = "NO_CRITICAL_PERIOD"
DESIGN_FAILURE = "DESIGN_FAILURE"
INCONCLUSIVE = "INCONCLUSIVE"

_MDE_SEARCH_CEILING = 10.0
_MDE_TOLERANCE = 1e-4


@dataclass(frozen=True)
class RunRecord:
    """One completed training run. Produced by the trainer, never edited by analysis.

    `total_steps` is the budget rung. Under the ladder endpoint it is a treatment variable,
    not a constant to be checked for equality across the grid.
    """

    condition: str
    seed: int
    final_eval_loss: float
    total_steps: int


@dataclass(frozen=True)
class LadderResult:
    condition: str
    budgets: tuple[int, ...]
    mean_gaps: tuple[float, ...]
    slope: float
    slope_p: float
    top_gap: float
    margin: float
    crossing_budget: float
    verdict: str

    @property
    def label(self) -> str:
        if self.verdict == DECAYING_UNRESOLVED and math.isfinite(self.crossing_budget):
            return f"{self.verdict} (reaches the margin near {self.crossing_budget:,.0f} steps)"
        return self.verdict


@dataclass(frozen=True)
class StudyResult:
    verdict: str
    reasons: tuple[str, ...]
    margin: float
    baseline_sd: float
    top_budget: int
    primary_delta: float
    primary_p_value: float
    primary_mde: float
    ladders: tuple[LadderResult, ...]


# --- Permutation machinery ---------------------------------------------------------


def exact_permutation_p(treatment: list[float], reference: list[float]) -> float:
    """One-sided exact permutation p-value for mean(treatment) > mean(reference).

    Enumerates every way of splitting the pooled values into groups of the observed sizes
    and counts the fraction whose mean difference is at least the observed one. The
    observed assignment is included in the count, so the p-value can never be zero.
    """
    if len(treatment) < 2 or len(reference) < 2:
        raise ValueError("each group needs at least two runs")

    pooled = list(treatment) + list(reference)
    observed = fmean(treatment) - fmean(reference)
    pooled_sum = math.fsum(pooled)
    k, m = len(treatment), len(reference)

    total = at_least = 0
    for idx in combinations(range(len(pooled)), k):
        left = math.fsum(pooled[i] for i in idx)
        total += 1
        if left / k - (pooled_sum - left) / m >= observed - 1e-12:
            at_least += 1
    return at_least / total


def _budget_label_assignments(counts: list[int], size: int):
    """Every distinct way of dealing budget labels with the observed multiplicities."""

    def walk(remaining: tuple[int, ...], slots: tuple[int, ...]):
        if not remaining:
            yield ()
            return
        first, rest = remaining[0], remaining[1:]
        for chosen in combinations(slots, first):
            leftover = tuple(s for s in slots if s not in chosen)
            for tail in walk(rest, leftover):
                yield (chosen,) + tail

    yield from walk(tuple(counts), tuple(range(size)))


def decay_slope_test(budgets: list[int], gaps: list[float]) -> tuple[float, float]:
    """Slope of gap against log2(budget), with a one-sided p-value for a negative slope.

    The null is that budget is unrelated to gap, so budget labels are exchangeable over the
    observed gaps. Because permuting labels leaves the budget multiset — and therefore the
    mean and spread of the x values — unchanged, the slope is a monotone function of the
    cross-product `sum(x_i * y_i)`, which is what the enumeration compares.

    A negative slope means the gap shrinks as the budget grows: the damage is being
    repaired, and what looked permanent was unfinished recovery.
    """
    if len(set(budgets)) < 2:
        raise ValueError("a decay test needs at least two budget rungs")
    if len(budgets) != len(gaps):
        raise ValueError("budgets and gaps must be parallel")

    xs = [math.log2(b) for b in budgets]
    x_mean, y_mean = fmean(xs), fmean(gaps)
    denominator = math.fsum((x - x_mean) ** 2 for x in xs)
    slope = math.fsum((x - x_mean) * (y - y_mean) for x, y in zip(xs, gaps)) / denominator

    distinct = sorted(set(xs))
    counts = [xs.count(value) for value in distinct]
    observed = math.fsum(x * y for x, y in zip(xs, gaps))

    total = at_most = 0
    for assignment in _budget_label_assignments(counts, len(xs)):
        statistic = 0.0
        for value, slots in zip(distinct, assignment):
            statistic += value * math.fsum(gaps[s] for s in slots)
        total += 1
        if statistic <= observed + 1e-12:
            at_most += 1
        if total >= MAX_ENUMERATED_ASSIGNMENTS:
            break

    return slope, at_most / total


def registered_margin(baseline_losses: list[float]) -> float:
    """The smallest difference this study is willing to call real.

    Three baseline seed standard deviations, floored at an absolute value so that an
    unusually tight baseline cannot let a scientifically empty difference through.
    """
    if len(baseline_losses) < 2:
        raise ValueError("margin needs at least two baseline seeds")
    return max(MARGIN_SD_MULTIPLE * stdev(baseline_losses), MARGIN_FLOOR_NATS)


def _p_at_shift(treatment: list[float], reference: list[float], shift: float) -> float:
    return exact_permutation_p([x + shift for x in treatment], reference)


def minimum_detectable_effect(
    treatment: list[float], reference: list[float], margin: float
) -> float:
    """Smallest true difference this comparison could have flagged.

    Shift the treatment values uniformly by `c` and ask for the smallest `c` at which the
    registered test rejects; the corresponding difference is `observed_delta + c`, floored
    at the margin. `c` may be negative: a comparison that already rejects could have
    detected something smaller than what it saw, and reporting its observed difference as
    its resolution would overstate how blunt the instrument is.

    Returns infinity when no shift reaches significance — the honest answer for a
    comparison too small to reject under any effect size.
    """
    if _p_at_shift(treatment, reference, 0.0) <= ALPHA:
        low, high = -1.0, 0.0
        while _p_at_shift(treatment, reference, low) <= ALPHA:
            high, low = low, low * 2
            if low < -_MDE_SEARCH_CEILING:
                break
    else:
        low, high = 0.0, 1.0
        while _p_at_shift(treatment, reference, high) > ALPHA:
            low, high = high, high * 2
            if high > _MDE_SEARCH_CEILING:
                return math.inf

    while high - low > _MDE_TOLERANCE:
        mid = (low + high) / 2
        if _p_at_shift(treatment, reference, mid) <= ALPHA:
            high = mid
        else:
            low = mid

    return max(fmean(treatment) - fmean(reference) + high, margin)


# --- Ladder analysis ---------------------------------------------------------------


def paired_gaps(records: list[RunRecord]) -> dict[str, dict[int, dict[int, float]]]:
    """Gap to the baseline, paired within budget and seed.

    Pairing matters: a seed fixes both the initialization and the data order, so the paired
    difference removes a variance component that an unpaired comparison would carry. A
    deficit run with no baseline at the same budget and seed has no gap and is dropped from
    the ladder — which is reported, never silent.
    """
    losses: dict[str, dict[int, dict[int, float]]] = {}
    for record in records:
        losses.setdefault(record.condition, {}).setdefault(record.total_steps, {})[
            record.seed
        ] = record.final_eval_loss

    baseline = losses.get(BASELINE, {})
    gaps: dict[str, dict[int, dict[int, float]]] = {}
    for condition, by_budget in losses.items():
        if condition == BASELINE:
            continue
        for budget, by_seed in by_budget.items():
            for seed, loss in by_seed.items():
                reference = baseline.get(budget, {}).get(seed)
                if reference is None:
                    continue
                gaps.setdefault(condition, {}).setdefault(budget, {})[seed] = loss - reference
    return gaps


def ladder_verdict(
    condition: str, gaps_by_budget: dict[int, dict[int, float]], margin: float
) -> LadderResult:
    """Does this condition's damage go away when the budget grows?

    Four outcomes, and the two in the middle are the ones that matter:

    - `TRANSIENT` — the gap shrinks with budget and is already under the margin at the top
      rung. Later training repaired the damage.
    - `PERSISTENT` — no detectable shrinkage and the gap is still over the margin. The
      damage survived every budget increase this ladder applied.
    - `DECAYING_UNRESOLVED` — shrinking but not yet under the margin. Reported with the
      budget at which the fitted line would cross, which is an extrapolation and is labelled
      as one.
    - `NO_EFFECT` — under the margin throughout; there was nothing to repair.
    """
    budgets = sorted(gaps_by_budget)
    flat_budgets = [b for b in budgets for _ in gaps_by_budget[b]]
    flat_gaps = [g for b in budgets for g in gaps_by_budget[b].values()]
    mean_gaps = tuple(fmean(gaps_by_budget[b].values()) for b in budgets)
    top_gap = mean_gaps[-1]

    if len(budgets) < 2 or len(flat_gaps) < 3:
        return LadderResult(
            condition, tuple(budgets), mean_gaps, math.nan, math.nan, top_gap,
            margin, math.inf, UNDETERMINED,
        )

    slope, slope_p = decay_slope_test(flat_budgets, flat_gaps)
    decaying = slope < 0 and slope_p <= ALPHA
    residual = top_gap >= margin

    crossing = math.inf
    if decaying and residual:
        # gap = intercept + slope * log2(budget); solve for gap == margin.
        xs = [math.log2(b) for b in flat_budgets]
        intercept = fmean(flat_gaps) - slope * fmean(xs)
        crossing = 2 ** ((margin - intercept) / slope)

    if decaying and not residual:
        verdict = TRANSIENT
    elif decaying:
        verdict = DECAYING_UNRESOLVED
    elif residual:
        verdict = PERSISTENT
    else:
        verdict = NO_EFFECT

    return LadderResult(
        condition, tuple(budgets), mean_gaps, slope, slope_p, top_gap, margin,
        crossing, verdict,
    )


def study_verdict(records: list[RunRecord]) -> StudyResult:
    """Apply the full registered decision procedure to a completed ladder."""
    non_finite = [r for r in records if not math.isfinite(r.final_eval_loss)]
    budgets = sorted({r.total_steps for r in records})
    baseline_top = [
        r.final_eval_loss
        for r in records
        if r.condition == BASELINE and r.total_steps == (budgets[-1] if budgets else None)
    ]

    failures: list[str] = []
    if non_finite:
        failures.append(
            f"{len(non_finite)} run(s) produced a non-finite loss: "
            + ", ".join(f"{r.condition}/seed{r.seed}" for r in non_finite)
        )
    if len(budgets) < 2:
        failures.append(f"a ladder needs at least two budget rungs, found {budgets}")
    if len(baseline_top) < 2:
        failures.append("fewer than two baseline runs at the top budget")

    if failures:
        return StudyResult(
            DESIGN_FAILURE, tuple(failures), math.nan, math.nan,
            budgets[-1] if budgets else 0, math.nan, math.nan, math.nan, (),
        )

    top = budgets[-1]
    margin = registered_margin(baseline_top)
    gaps = paired_gaps(records)
    ladders = tuple(
        ladder_verdict(condition, gaps[condition], margin) for condition in sorted(gaps)
    )
    by_condition = {ladder.condition: ladder for ladder in ladders}

    reasons: list[str] = []
    controls = [
        ladder for ladder in ladders
        if ladder.condition.startswith(NEGATIVE_CONTROL_PREFIX)
    ]
    broken = [c for c in controls if c.verdict in (PERSISTENT, UNDETERMINED)]
    if not controls:
        return StudyResult(
            DESIGN_FAILURE, ("no negative control ladder present",), margin,
            stdev(baseline_top), top, math.nan, math.nan, math.nan, ladders,
        )
    if broken:
        return StudyResult(
            DESIGN_FAILURE,
            tuple(
                f"negative control {c.condition} returned {c.verdict}: its damage did not "
                f"decay away, so a scar elsewhere is not attributable to the deficit type"
                for c in broken
            ),
            margin, stdev(baseline_top), top, math.nan, math.nan, math.nan, ladders,
        )

    early = gaps.get(PRIMARY_EARLY, {}).get(top, {})
    late = gaps.get(PRIMARY_LATE, {}).get(top, {})
    if len(early) < 2 or len(late) < 2:
        return StudyResult(
            DESIGN_FAILURE,
            ("the primary contrast lacks runs at the top budget",),
            margin, stdev(baseline_top), top, math.nan, math.nan, math.nan, ladders,
        )

    early_gaps, late_gaps = list(early.values()), list(late.values())
    primary_delta = fmean(early_gaps) - fmean(late_gaps)
    primary_p = exact_permutation_p(early_gaps, late_gaps)
    primary_mde = minimum_detectable_effect(early_gaps, late_gaps, margin)

    early_ladder = by_condition.get(PRIMARY_EARLY)
    early_survives = early_ladder is not None and early_ladder.verdict in (
        PERSISTENT,
        DECAYING_UNRESOLVED,
    )

    if early_survives and primary_p <= ALPHA and primary_delta >= margin:
        verdict = CRITICAL_PERIOD
        reasons.append(
            f"{PRIMARY_EARLY} returned {early_ladder.verdict} and exceeded {PRIMARY_LATE} "
            f"at the top budget by {primary_delta:.4f} nats (p {primary_p:.4f})"
        )
    elif primary_p > ALPHA and primary_mde <= margin:
        verdict = NO_CRITICAL_PERIOD
        reasons.append(
            f"onset made no detectable difference at {top:,} steps (p {primary_p:.4f}) at a "
            f"resolution (MDE {primary_mde:.4f}) at or below the margin {margin:.4f}"
        )
        if early_ladder is not None and early_ladder.verdict in (TRANSIENT, NO_EFFECT):
            reasons.append(
                f"{PRIMARY_EARLY} returned {early_ladder.verdict}: early damage was "
                "repaired by later training rather than persisting"
            )
    else:
        verdict = INCONCLUSIVE
        if not early_survives and early_ladder is not None:
            reasons.append(
                f"{PRIMARY_EARLY} returned {early_ladder.verdict}, so there is no "
                "persistent early damage for an onset effect to be about"
            )
        if primary_p > ALPHA:
            reasons.append(
                f"primary contrast did not reject (p {primary_p:.4f}) and its MDE "
                f"{primary_mde:.4f} exceeds the margin {margin:.4f}"
            )
        elif primary_delta < margin:
            reasons.append(
                f"primary delta {primary_delta:.4f} is below the margin {margin:.4f}"
            )

    return StudyResult(
        verdict, tuple(reasons), margin, stdev(baseline_top), top,
        primary_delta, primary_p, primary_mde, ladders,
    )

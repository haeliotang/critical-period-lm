"""Frozen decision rules for the critical-period study.

This module is part of the freeze corpus. Once `freeze-manifest.json` is tagged, any
change here invalidates the freeze and requires a new design version.

Everything here is a pure function over run records. Nothing reads the filesystem, nothing
touches a model, and nothing is random.

## The endpoint estimates a decay law

The study reports **how damage decays with training budget**, not a categorical verdict at
one budget. For each condition the gap to a seed-matched baseline is fitted as

    gap(T) = c / T^alpha

and `alpha` is the registered quantity. It has a reading that does not depend on any
threshold we chose:

    alpha = 1  the gap falls as 1/T -- exactly what a pure lag predicts, damage that is
               nothing but training time not yet made up
    alpha = 0  the gap does not move -- permanent damage
    0 < alpha < 1  decays, but more slowly than lost training would explain

Two earlier endpoints failed and both failures are recorded in `deviations/`. A level at one
budget could not tell a scar from unfinished recovery. A categorical ladder verdict fixed
that but made every answer hinge on an arbitrary 0.01-nat floor, and it went blind exactly
where the conditions converged in level: in ladder 1 the top-rung contrast was +0.0003 nats
at p = 0.50 while the decay exponents differed by 0.276. The level had lost the difference
that the rate still held.

Seeds are the replication unit: each seed gives one independent fit, and inference is across
seeds. The interval on `alpha` is a t-interval, which is a normality assumption at four or
five seeds. That is this design's weakest link and it is declared rather than buried.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations
from statistics import fmean, stdev

# --- Registered constants. Frozen. -------------------------------------------------

ALPHA = 0.05

# Level floor, used only to decide whether a condition did any damage worth modelling.
# It no longer decides any verdict, which is the point of moving to an estimate.
LEVEL_MARGIN_SD_MULTIPLE = 3.0
LEVEL_MARGIN_FLOOR_NATS = 0.01

# Smallest difference in decay exponent the study is willing to call real. Self-calibrating:
# three times the control's own seed spread, floored. The control is the natural noise
# reference because it is the condition whose exponent the design predicts is exactly 1.
EXPONENT_MARGIN_SD_MULTIPLE = 3.0
EXPONENT_MARGIN_FLOOR = 0.10

PURE_LAG_EXPONENT = 1.0

BASELINE = "baseline"
PRIMARY_EARLY = "shuffle_early_N4"
PRIMARY_LATE = "shuffle_late_N4"
NEGATIVE_CONTROL_PREFIX = "fixed_early_"

# Per-condition readings of the fitted exponent.
LAG = "LAG"
SUBLINEAR = "SUBLINEAR"
PERSISTENT = "PERSISTENT"
NO_EFFECT = "NO_EFFECT"
UNDETERMINED = "UNDETERMINED"

# Study verdicts.
CRITICAL_PERIOD = "CRITICAL_PERIOD"
NO_CRITICAL_PERIOD = "NO_CRITICAL_PERIOD"
REVERSE_ONSET_EFFECT = "REVERSE_ONSET_EFFECT"
DESIGN_FAILURE = "DESIGN_FAILURE"
INCONCLUSIVE = "INCONCLUSIVE"

# Two-sided 95% t critical values by degrees of freedom. Tabulated rather than computed so
# that the frozen module carries no dependency; beyond the table the normal value is used.
_T_CRITICAL = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145,
    15: 2.131, 16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
}
_Z_CRITICAL = 1.960


@dataclass(frozen=True)
class RunRecord:
    """One completed training run. Produced by the trainer, never edited by analysis.

    `total_steps` is the budget rung. Under a decay endpoint it is the independent variable,
    not a constant to be checked for equality.
    """

    condition: str
    seed: int
    final_eval_loss: float
    total_steps: int


@dataclass(frozen=True)
class DecayFit:
    condition: str
    budgets: tuple[int, ...]
    mean_gaps: tuple[float, ...]
    seeds_fitted: int
    seeds_dropped: int
    alpha: float
    alpha_low: float
    alpha_high: float
    per_seed_alpha: tuple[float, ...]
    top_gap: float
    crossing_budget: float
    reading: str

    @property
    def label(self) -> str:
        if self.reading == LAG:
            return "LAG (consistent with pure lost training)"
        if self.reading == SUBLINEAR:
            return "SUBLINEAR (decays, but slower than lost training explains)"
        return self.reading


@dataclass(frozen=True)
class StudyResult:
    verdict: str
    reasons: tuple[str, ...]
    level_margin: float
    exponent_margin: float
    baseline_sd: float
    top_budget: int
    primary_delta: float
    primary_p_one_sided: float
    primary_p_two_sided: float
    fits: tuple[DecayFit, ...]


# --- Primitives --------------------------------------------------------------------


def exact_permutation_p(
    treatment: list[float], reference: list[float], two_sided: bool = False
) -> float:
    """Exact permutation p-value for a difference in means.

    One-sided by default, for `mean(treatment) > mean(reference)`. Enumerates every split of
    the pooled values into groups of the observed sizes; the observed assignment is counted,
    so the p-value is never zero.
    """
    if len(treatment) < 2 or len(reference) < 2:
        raise ValueError("each group needs at least two seeds")

    pooled = list(treatment) + list(reference)
    observed = fmean(treatment) - fmean(reference)
    pooled_sum = math.fsum(pooled)
    k, m = len(treatment), len(reference)

    total = extreme = 0
    for idx in combinations(range(len(pooled)), k):
        left = math.fsum(pooled[i] for i in idx)
        statistic = left / k - (pooled_sum - left) / m
        total += 1
        if two_sided:
            if abs(statistic) >= abs(observed) - 1e-12:
                extreme += 1
        elif statistic >= observed - 1e-12:
            extreme += 1
    return extreme / total


def t_interval(values: list[float]) -> tuple[float, float, float]:
    """Mean and two-sided 95% t-interval. Returns (mean, low, high).

    A normality assumption at the seed counts this study can afford. Declared in the module
    docstring and in `preregistration.md`; it is not disguised as an exact procedure.
    """
    n = len(values)
    if n < 2:
        return (values[0] if values else math.nan, -math.inf, math.inf)
    mean = fmean(values)
    spread = stdev(values)
    critical = _T_CRITICAL.get(n - 1, _Z_CRITICAL)
    half = critical * spread / math.sqrt(n)
    return mean, mean - half, mean + half


def level_margin(baseline_losses: list[float]) -> float:
    """Smallest gap worth modelling at all. Three baseline seed SDs, floored."""
    if len(baseline_losses) < 2:
        raise ValueError("margin needs at least two baseline seeds")
    return max(LEVEL_MARGIN_SD_MULTIPLE * stdev(baseline_losses), LEVEL_MARGIN_FLOOR_NATS)


def fit_exponent(budgets: list[int], gaps: list[float]) -> float:
    """Decay exponent from one seed: slope of -log(gap) against log(budget).

    Requires strictly positive gaps. A non-positive gap means the deficit run beat its own
    baseline at that rung, which is noise around zero rather than decay, and the seed is
    reported as dropped rather than nudged into the logarithm.
    """
    if len(budgets) < 2:
        raise ValueError("an exponent needs at least two budget rungs")
    if any(g <= 0 for g in gaps):
        raise ValueError("exponent fitting requires strictly positive gaps")

    xs = [math.log(b) for b in budgets]
    ys = [math.log(g) for g in gaps]
    x_mean, y_mean = fmean(xs), fmean(ys)
    denominator = math.fsum((x - x_mean) ** 2 for x in xs)
    return -math.fsum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator


def crossing_budget(budgets: list[int], gaps: list[float], target: float) -> float:
    """Budget at which the fitted power law reaches `target`.

    Computed from the power law rather than from a line in log-budget. The earlier
    log-linear form predicted negative gaps one rung beyond the data and understated this
    quantity roughly twofold; it was the wrong functional form, not merely an imprecise one.
    """
    try:
        alpha = fit_exponent(budgets, gaps)
    except ValueError:
        return math.inf
    if alpha <= 0:
        return math.inf
    xs = [math.log(b) for b in budgets]
    ys = [math.log(g) for g in gaps]
    log_c = fmean(ys) + alpha * fmean(xs)
    return math.exp((log_c - math.log(target)) / alpha)


# --- Ladder analysis ---------------------------------------------------------------


def paired_gaps(records: list[RunRecord]) -> dict[str, dict[int, dict[int, float]]]:
    """Gap to the baseline, paired within budget and seed.

    A seed fixes the initialization and the data order, so pairing removes a variance
    component an unpaired comparison would carry. A deficit run with no baseline partner at
    the same budget and seed has no gap and is dropped — reported, never silent.
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


def fit_condition(
    condition: str, gaps_by_budget: dict[int, dict[int, float]], level: float
) -> DecayFit:
    """Estimate the decay exponent for one condition, seeds as the replication unit.

    Readings, from the interval on `alpha`:

    - `NO_EFFECT` — the top-rung gap is under the level floor; there was no damage to model,
      and fitting a decay to noise would invent a number.
    - `LAG` — the interval covers 1 and excludes 0. The gap falls as fast as lost training
      alone would explain: repairable damage, nothing left over.
    - `SUBLINEAR` — the interval lies entirely below 1 and above 0. It decays, but more
      slowly than a pure lag, so something outlasts the training it cost.
    - `PERSISTENT` — the interval covers 0. No detectable decay.
    - `UNDETERMINED` — the interval spans both 0 and 1 and settles nothing.
    """
    budgets = sorted(gaps_by_budget)
    mean_gaps = tuple(fmean(gaps_by_budget[b].values()) for b in budgets)
    top_gap = mean_gaps[-1] if mean_gaps else math.nan

    seeds = set.intersection(*(set(gaps_by_budget[b]) for b in budgets)) if budgets else set()
    per_seed: list[float] = []
    dropped = 0
    for seed in sorted(seeds):
        values = [gaps_by_budget[b][seed] for b in budgets]
        try:
            per_seed.append(fit_exponent(budgets, values))
        except ValueError:
            dropped += 1

    def result(alpha, low, high, reading, crossing=math.inf):
        return DecayFit(
            condition, tuple(budgets), mean_gaps, len(per_seed), dropped,
            alpha, low, high, tuple(per_seed), top_gap, crossing, reading,
        )

    if len(budgets) < 2 or len(per_seed) < 2:
        return result(math.nan, math.nan, math.nan, UNDETERMINED)
    if top_gap < level:
        return result(math.nan, math.nan, math.nan, NO_EFFECT)

    alpha, low, high = t_interval(per_seed)
    crossing = crossing_budget(
        budgets, [fmean(gaps_by_budget[b].values()) for b in budgets], level
    )

    if low <= 0:
        reading = PERSISTENT if high < PURE_LAG_EXPONENT else UNDETERMINED
    elif high < PURE_LAG_EXPONENT:
        reading = SUBLINEAR
    elif low <= PURE_LAG_EXPONENT <= high:
        reading = LAG
    else:
        # Interval entirely above 1: decays faster than a pure lag. Not a failure mode the
        # design predicts, so it is not given a flattering name.
        reading = UNDETERMINED

    return result(alpha, low, high, reading, crossing)


def study_verdict(records: list[RunRecord]) -> StudyResult:
    """Apply the full registered decision procedure to a completed ladder."""
    non_finite = [r for r in records if not math.isfinite(r.final_eval_loss)]
    budgets = sorted({r.total_steps for r in records})
    top = budgets[-1] if budgets else 0
    baseline_top = [
        r.final_eval_loss for r in records if r.condition == BASELINE and r.total_steps == top
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

    def failed(reasons, level=math.nan, exponent=math.nan, sd=math.nan, fits=()):
        return StudyResult(
            DESIGN_FAILURE, tuple(reasons), level, exponent, sd, top,
            math.nan, math.nan, math.nan, fits,
        )

    if failures:
        return failed(failures)

    level = level_margin(baseline_top)
    gaps = paired_gaps(records)
    fits = tuple(fit_condition(c, gaps[c], level) for c in sorted(gaps))
    by_condition = {fit.condition: fit for fit in fits}

    controls = [f for f in fits if f.condition.startswith(NEGATIVE_CONTROL_PREFIX)]
    if not controls:
        return failed(["no negative control present"], level, math.nan, stdev(baseline_top), fits)

    # The control's own seed spread sets the smallest exponent difference worth believing.
    control_alphas = [a for c in controls for a in c.per_seed_alpha]
    if len(control_alphas) < 2:
        return failed(
            ["the negative control could not be fitted, so no exponent scale exists"],
            level, math.nan, stdev(baseline_top), fits,
        )
    exponent = max(
        EXPONENT_MARGIN_SD_MULTIPLE * stdev(control_alphas), EXPONENT_MARGIN_FLOOR
    )

    misbehaving = [c for c in controls if c.reading not in (LAG, NO_EFFECT)]
    if misbehaving:
        return failed(
            [
                f"negative control {c.condition} read {c.reading} with alpha "
                f"{c.alpha:.3f} [{c.alpha_low:.3f}, {c.alpha_high:.3f}]: the measurement "
                f"itself does not behave as a pure lag, so a departure from one elsewhere "
                f"is not attributable to the deficit"
                for c in misbehaving
            ],
            level, exponent, stdev(baseline_top), fits,
        )

    early = by_condition.get(PRIMARY_EARLY)
    late = by_condition.get(PRIMARY_LATE)
    if early is None or late is None or len(early.per_seed_alpha) < 2 or len(late.per_seed_alpha) < 2:
        return failed(
            ["the primary contrast could not be fitted at both onsets"],
            level, exponent, stdev(baseline_top), fits,
        )

    early_alphas, late_alphas = list(early.per_seed_alpha), list(late.per_seed_alpha)
    delta = fmean(early_alphas) - fmean(late_alphas)

    # A critical period predicts early damage is the harder to repair, so its gap decays
    # more slowly: alpha_early < alpha_late. The primary test is one-sided in that
    # theory-predicted direction. The two-sided test is secondary and exists so that an
    # onset effect running the other way is reported rather than absorbed into a null.
    primary_p = exact_permutation_p(late_alphas, early_alphas)
    two_sided_p = exact_permutation_p(early_alphas, late_alphas, two_sided=True)

    reasons: list[str] = []
    early_repairable = early.reading in (LAG, NO_EFFECT)

    if primary_p <= ALPHA and -delta >= exponent:
        verdict = CRITICAL_PERIOD
        reasons.append(
            f"{PRIMARY_EARLY} decayed more slowly than {PRIMARY_LATE} by "
            f"{-delta:.3f} in exponent (one-sided p {primary_p:.4f})"
        )
    elif two_sided_p <= ALPHA and delta >= exponent:
        verdict = REVERSE_ONSET_EFFECT
        reasons.append(
            f"onset mattered in the direction opposite to a critical period: "
            f"{PRIMARY_LATE} decayed more slowly than {PRIMARY_EARLY} by {delta:.3f} in "
            f"exponent (two-sided p {two_sided_p:.4f}). Late damage outlasts early damage, "
            f"which no critical-period account predicts"
        )
    elif two_sided_p > ALPHA and abs(delta) < exponent:
        verdict = NO_CRITICAL_PERIOD
        reasons.append(
            f"onset made no difference to the decay exponent: delta {delta:+.3f} against a "
            f"margin of {exponent:.3f} (two-sided p {two_sided_p:.4f})"
        )
    else:
        verdict = INCONCLUSIVE
        reasons.append(
            f"exponent delta {delta:+.3f} and two-sided p {two_sided_p:.4f} settle neither "
            f"an onset effect nor its absence against a margin of {exponent:.3f}"
        )

    if early_repairable and verdict != CRITICAL_PERIOD:
        reasons.append(
            f"{PRIMARY_EARLY} read {early.reading}: early damage decays as fast as the "
            "training it cost, so it is repairable rather than permanent"
        )

    return StudyResult(
        verdict, tuple(reasons), level, exponent, stdev(baseline_top), top,
        delta, primary_p, two_sided_p, fits,
    )

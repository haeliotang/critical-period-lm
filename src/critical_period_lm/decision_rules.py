"""Frozen decision rules for the critical-period study.

This module is part of the freeze corpus. Once `freeze-manifest.json` is tagged, any
change here invalidates the freeze and requires a new design version.

Everything here is a pure function over run records. Nothing reads the filesystem, nothing
touches a model, and nothing is random.

## The endpoint estimates a decay law

The study reports **how damage decays with training budget**, not a categorical verdict at
one budget. For each condition the gap to a seed-matched baseline is fitted as

    gap(T) = c / T^alpha

and `alpha` is the registered quantity: how fast the damage is repaired as the budget grows.

## The control is the anchor, and the absolute question is out of scope

`alpha` is not read against a theoretical value. It is read against the negative control's
own exponent, measured in the same experiment.

The reason is that `alpha` mixes two things: `gap = b(T) · delta_eff / T`, where `b` is the
baseline curve's local log-slope and `delta_eff` is the deficit's actual cost in effective
training steps. Ladder 2 measured `b` falling 30% per doubling, so an anchor of
`alpha = 1` — which assumes `b` constant — is wrong, and the corrected value of about 1.5
rests on two slope estimates from three points and is too fragile to replace it. `b(T)` is
common to every condition at a rung, so it cancels in a comparison and cancels nowhere else.

**What this design therefore cannot answer.** Whether damage is a lag or a scar is an
absolute question, and answering it needs `delta_eff` held constant across rungs. Estimating
`delta_eff` requires inverting the baseline curve, which three rungs cannot pin down —
ladder 2 gave 1370, 693, 882 effective steps for the control, a non-monotonicity that is an
artefact of interpolating between three points. That question needs a denser ladder and is
out of scope here. It is dropped, not answered.

**What it can answer**, and what the primary contrast asks, is comparative: does onset change
the rate at which damage is repaired. That needs no anchor at all, being a difference of two
exponents, and it is immune to a constant proportional handicap on either arm — such a
handicap moves the amplitude `c` and leaves `alpha` alone.

Three earlier endpoints failed and all three are recorded in `deviations/`. Each smuggled in
a parameter from outside the experiment: where the run happened to stop, an arbitrary
0.01-nat floor, and a theoretical `alpha = 1`. A control-anchored comparison smuggles in
nothing — every quantity it uses is measured in the same runs.

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

# Descriptive only. Reported beside every exponent, never gated on. `alpha = 1` is what a
# pure lag gives when the baseline curve's log-slope is constant, which ladder 2 showed it
# is not.
NAIVE_PURE_LAG_EXPONENT = 1.0

BASELINE = "baseline"
PRIMARY_EARLY = "shuffle_early_N4"
PRIMARY_LATE = "shuffle_late_N4"
NEGATIVE_CONTROL_PREFIX = "fixed_early_"

# Per-condition readings, taken against the control rather than against theory.
ANCHOR = "ANCHOR"
LIKE_CONTROL = "LIKE_CONTROL"
SLOWER_THAN_CONTROL = "SLOWER_THAN_CONTROL"
FASTER_THAN_CONTROL = "FASTER_THAN_CONTROL"
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
    delta_vs_control: float
    p_vs_control: float
    reading: str

    @property
    def label(self) -> str:
        return {
            ANCHOR: "ANCHOR (the reference every other condition is read against)",
            LIKE_CONTROL: "LIKE_CONTROL (repairs at the control's rate)",
            SLOWER_THAN_CONTROL: "SLOWER_THAN_CONTROL (repairs more slowly than the control)",
            FASTER_THAN_CONTROL: "FASTER_THAN_CONTROL (repairs faster than the control)",
        }.get(self.reading, self.reading)


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
    baseline_log_slopes: tuple[float, ...]
    implied_pure_lag_exponent: float
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
    docstring and in `preregistration.md`; it is not disguised as an exact procedure, and the
    primary contrast does not rest on it.
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


def baseline_log_slopes(baseline_by_budget: dict[int, float]) -> tuple[float, ...]:
    """Local log-slope `b` of the baseline curve between consecutive rungs.

    Descriptive. Reported because the naive `alpha = 1` anchor assumes these are equal, and
    ladder 2 measured them falling 30% per doubling. Reporting them lets a reader see the
    assumption fail rather than take it on trust.
    """
    rungs = sorted(baseline_by_budget)
    return tuple(
        (baseline_by_budget[lo] - baseline_by_budget[hi]) / math.log(hi / lo)
        for lo, hi in zip(rungs, rungs[1:])
    )


def implied_pure_lag_exponent(slopes: tuple[float, ...], rungs: tuple[int, ...]) -> float:
    """What exponent a pure lag would give, given how the baseline slope actually moves.

    `gap = b(T)·delta/T`, so a falling `b` makes a pure lag decay faster than `1/T`. This is
    the corrected anchor, and it is reported and never gated on: it rests on `len(slopes)`
    estimates from `len(rungs)` points and is far too fragile to decide anything.
    """
    if len(slopes) < 2:
        return math.nan
    span = math.log(rungs[-1] / rungs[0]) / (len(slopes) - 1) if len(rungs) > 1 else math.nan
    return 1.0 - math.log(slopes[-1] / slopes[0]) / span


# --- Ladder analysis ---------------------------------------------------------------


def paired_gaps(records: list[RunRecord]) -> dict[str, dict[int, dict[int, float]]]:
    """Gap to the baseline, paired within budget and seed.

    A seed fixes the initialization and the data order, so pairing removes a variance
    component an unpaired comparison would carry. A deficit run with no baseline partner at
    the same budget and seed has no gap and is dropped -- reported, never silent.
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
    """Fit one condition's decay exponent, seeds as the replication unit.

    No reading is assigned here: a reading requires the control, and the control is not known
    to this function. `study_verdict` assigns readings once all conditions are fitted.
    """
    budgets = sorted(gaps_by_budget)
    mean_gaps = tuple(fmean(gaps_by_budget[b].values()) for b in budgets)
    top_gap = mean_gaps[-1] if mean_gaps else math.nan

    seeds = set.intersection(*(set(gaps_by_budget[b]) for b in budgets)) if budgets else set()
    per_seed: list[float] = []
    dropped = 0
    for seed in sorted(seeds):
        try:
            per_seed.append(fit_exponent(budgets, [gaps_by_budget[b][seed] for b in budgets]))
        except ValueError:
            dropped += 1

    def result(alpha, low, high, reading):
        return DecayFit(
            condition, tuple(budgets), mean_gaps, len(per_seed), dropped,
            alpha, low, high, tuple(per_seed), top_gap, math.nan, math.nan, reading,
        )

    if len(budgets) < 2 or len(per_seed) < 2:
        return result(math.nan, math.nan, math.nan, UNDETERMINED)
    if top_gap < level:
        return result(math.nan, math.nan, math.nan, NO_EFFECT)
    return result(*t_interval(per_seed), UNDETERMINED)


def read_against_control(fit: DecayFit, control_alphas: list[float], margin: float) -> DecayFit:
    """Assign a reading by comparing this condition's exponent with the control's.

    The control absorbs whatever the measurement does to every condition alike -- the
    baseline curve's shape most of all -- so a difference from it is a difference in the
    deficit, which is the only thing this design claims to measure.
    """
    if fit.reading == NO_EFFECT or len(fit.per_seed_alpha) < 2:
        return fit

    per_seed = list(fit.per_seed_alpha)
    delta = fmean(per_seed) - fmean(control_alphas)
    p_value = exact_permutation_p(per_seed, control_alphas, two_sided=True)

    if abs(delta) < margin and p_value > ALPHA:
        reading = LIKE_CONTROL
    elif p_value <= ALPHA and delta <= -margin:
        reading = SLOWER_THAN_CONTROL
    elif p_value <= ALPHA and delta >= margin:
        reading = FASTER_THAN_CONTROL
    else:
        reading = UNDETERMINED

    return DecayFit(
        fit.condition, fit.budgets, fit.mean_gaps, fit.seeds_fitted, fit.seeds_dropped,
        fit.alpha, fit.alpha_low, fit.alpha_high, fit.per_seed_alpha, fit.top_gap,
        delta, p_value, reading,
    )


def study_verdict(records: list[RunRecord]) -> StudyResult:
    """Apply the full registered decision procedure to a completed ladder."""
    non_finite = [r for r in records if not math.isfinite(r.final_eval_loss)]
    budgets = sorted({r.total_steps for r in records})
    top = budgets[-1] if budgets else 0
    baseline_by_budget = {}
    for b in budgets:
        values = [r.final_eval_loss for r in records
                  if r.condition == BASELINE and r.total_steps == b and math.isfinite(r.final_eval_loss)]
        if values:
            baseline_by_budget[b] = fmean(values)
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
            math.nan, math.nan, math.nan, (), math.nan, fits,
        )

    if failures:
        return failed(failures)

    level = level_margin(baseline_top)
    slopes = baseline_log_slopes(baseline_by_budget)
    implied = implied_pure_lag_exponent(slopes, tuple(budgets))
    gaps = paired_gaps(records)
    fits = [fit_condition(c, gaps[c], level) for c in sorted(gaps)]

    controls = [f for f in fits if f.condition.startswith(NEGATIVE_CONTROL_PREFIX)]
    usable = [c for c in controls if len(c.per_seed_alpha) >= 2 and c.reading != NO_EFFECT]
    if not usable:
        return failed(
            [
                "no usable negative control: the control anchors every reading, so without "
                "a fitted control exponent nothing else can be read"
            ],
            level, math.nan, stdev(baseline_top), tuple(fits),
        )

    control_alphas = [a for c in usable for a in c.per_seed_alpha]
    exponent = max(EXPONENT_MARGIN_SD_MULTIPLE * stdev(control_alphas), EXPONENT_MARGIN_FLOOR)

    control_names = {c.condition for c in usable}
    fits = tuple(
        DecayFit(
            f.condition, f.budgets, f.mean_gaps, f.seeds_fitted, f.seeds_dropped, f.alpha,
            f.alpha_low, f.alpha_high, f.per_seed_alpha, f.top_gap, 0.0, 1.0, ANCHOR,
        )
        if f.condition in control_names
        else read_against_control(f, control_alphas, exponent)
        for f in fits
    )
    by_condition = {f.condition: f for f in fits}

    early = by_condition.get(PRIMARY_EARLY)
    late = by_condition.get(PRIMARY_LATE)
    if (
        early is None or late is None
        or len(early.per_seed_alpha) < 2 or len(late.per_seed_alpha) < 2
    ):
        return StudyResult(
            DESIGN_FAILURE, ("the primary contrast could not be fitted at both onsets",),
            level, exponent, stdev(baseline_top), top, math.nan, math.nan, math.nan,
            slopes, implied, fits,
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
    if primary_p <= ALPHA and -delta >= exponent:
        verdict = CRITICAL_PERIOD
        reasons.append(
            f"{PRIMARY_EARLY} repaired more slowly than {PRIMARY_LATE} by {-delta:.3f} in "
            f"exponent (one-sided p {primary_p:.4f})"
        )
    elif two_sided_p <= ALPHA and delta >= exponent:
        verdict = REVERSE_ONSET_EFFECT
        reasons.append(
            f"onset mattered in the direction opposite to a critical period: "
            f"{PRIMARY_LATE} repaired more slowly than {PRIMARY_EARLY} by {delta:.3f} in "
            f"exponent (two-sided p {two_sided_p:.4f}). Late damage outlasts early damage, "
            f"which no critical-period account predicts"
        )
    elif two_sided_p > ALPHA and abs(delta) < exponent:
        verdict = NO_CRITICAL_PERIOD
        reasons.append(
            f"onset made no difference to the repair rate: delta {delta:+.3f} against a "
            f"margin of {exponent:.3f} (two-sided p {two_sided_p:.4f})"
        )
    else:
        verdict = INCONCLUSIVE
        reasons.append(
            f"exponent delta {delta:+.3f} and two-sided p {two_sided_p:.4f} settle neither "
            f"an onset effect nor its absence against a margin of {exponent:.3f}"
        )

    if early.reading == LIKE_CONTROL and verdict != CRITICAL_PERIOD:
        reasons.append(
            f"{PRIMARY_EARLY} read {LIKE_CONTROL}: early damage is repaired at the same rate "
            "as the information-preserving control"
        )

    return StudyResult(
        verdict, tuple(reasons), level, exponent, stdev(baseline_top), top,
        delta, primary_p, two_sided_p, slopes, implied, fits,
    )

"""Frozen decision rules for the critical-period study.

This module is part of the freeze corpus. Once `freeze-manifest.json` is tagged, any
change here invalidates the freeze and requires a new design version.

Everything here is a pure function over run records. Nothing reads the filesystem, nothing
touches a model, and nothing is random: the tests are exact enumerations, so a verdict is
reproducible from the records alone.

Sample sizes in this study are 3 to 5 runs per cell. Normal-theory tests are not
defensible at that size, so every comparison is an exact one-sided permutation test over
the full set of label assignments. With 4 versus 4 the smallest attainable p-value is
1/70 ~ 0.014; with 3 versus 5 it is 1/56 ~ 0.018; with 3 versus 3 it is 1/20 = 0.05, which
is why the primary cells carry four seeds.
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
RECOVERY_MULTIPLIER = 2.0

BASELINE = "baseline"
PRIMARY_EARLY = "shuffle_early_N4"
PRIMARY_LATE = "shuffle_late_N4"
NEGATIVE_CONTROL_PREFIX = "permute_early_"

SCAR = "SCAR"
RECOVERED = "RECOVERED"
INCONCLUSIVE = "INCONCLUSIVE"

CRITICAL_PERIOD = "CRITICAL_PERIOD"
NO_CRITICAL_PERIOD = "NO_CRITICAL_PERIOD"
DESIGN_FAILURE = "DESIGN_FAILURE"

# Search bound for the minimum detectable effect, in nats per token. A cell needing more
# than this to reach significance is reported as unbounded rather than silently clipped.
_MDE_SEARCH_CEILING = 10.0
_MDE_TOLERANCE = 1e-4


@dataclass(frozen=True)
class RunRecord:
    """One completed training run. Produced by the trainer, never edited by analysis."""

    condition: str
    seed: int
    final_eval_loss: float
    total_steps: int


@dataclass(frozen=True)
class CellResult:
    condition: str
    n: int
    delta: float
    p_value: float
    margin: float
    mde: float
    verdict: str
    underpowered: bool

    @property
    def label(self) -> str:
        if self.verdict == RECOVERED and self.underpowered:
            return "calibrated null (underpowered)"
        return self.verdict


@dataclass(frozen=True)
class StudyResult:
    verdict: str
    reasons: tuple[str, ...]
    margin: float
    baseline_mean: float
    baseline_sd: float
    primary_delta: float
    primary_p_value: float
    primary_mde: float
    cells: tuple[CellResult, ...]


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
    total = 0
    at_least = 0
    pooled_sum = math.fsum(pooled)
    k = len(treatment)
    m = len(reference)

    for idx in combinations(range(len(pooled)), k):
        left = math.fsum(pooled[i] for i in idx)
        stat = left / k - (pooled_sum - left) / m
        total += 1
        # Tolerance guards against ties that float arithmetic would otherwise split.
        if stat >= observed - 1e-12:
            at_least += 1

    return at_least / total


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
    """Smallest true difference this comparison could have flagged as a scar.

    Shift the treatment losses uniformly by `c` and ask for the smallest `c` at which the
    registered test rejects; the corresponding difference is `observed_delta + c`. The
    minimum detectable effect is that difference, floored at the margin, since a scar must
    clear both bars. `c` is allowed to be negative: a cell that already rejects could have
    detected something smaller than what it saw, and reporting its observed delta as its
    resolution would overstate how blunt the instrument is.

    Found by bisection, which assumes the p-value is non-increasing in the shift. The
    assumption is checked directly in the test suite rather than taken on faith.

    Returns infinity when no shift reaches significance. That is the honest answer for a
    comparison too small to reject under any effect size: 2 versus 2 runs bottoms out at
    p = 1/6, so it can never clear alpha no matter how far the groups separate.
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

    observed_delta = fmean(treatment) - fmean(reference)
    return max(observed_delta + high, margin)


def cell_verdict(
    condition: str, cell_losses: list[float], baseline_losses: list[float], margin: float
) -> CellResult:
    """Verdict for one deficit cell against the baseline.

    RECOVERED means the cell failed to show a scar at this power. It does not mean no scar
    exists, which is why every RECOVERED cell carries its minimum detectable effect and is
    relabeled a calibrated null when that quantity exceeds the margin.
    """
    delta = fmean(cell_losses) - fmean(baseline_losses)
    p_value = exact_permutation_p(cell_losses, baseline_losses)
    mde = minimum_detectable_effect(cell_losses, baseline_losses, margin)

    if delta >= margin and p_value <= ALPHA:
        verdict = SCAR
    elif delta >= margin:
        verdict = INCONCLUSIVE
    else:
        verdict = RECOVERED

    return CellResult(
        condition=condition,
        n=len(cell_losses),
        delta=delta,
        p_value=p_value,
        margin=margin,
        mde=mde,
        verdict=verdict,
        underpowered=mde > margin,
    )


def _mechanical_failures(records: list[RunRecord]) -> list[str]:
    reasons = []
    if not any(math.isfinite(r.final_eval_loss) for r in records):
        return ["no run produced a finite loss"]

    non_finite = [r for r in records if not math.isfinite(r.final_eval_loss)]
    if non_finite:
        reasons.append(
            f"{len(non_finite)} run(s) produced a non-finite loss: "
            + ", ".join(f"{r.condition}/seed{r.seed}" for r in non_finite)
        )

    step_counts = {r.total_steps for r in records}
    if len(step_counts) > 1:
        reasons.append(f"total_steps is not identical across runs: {sorted(step_counts)}")

    return reasons


def study_verdict(
    records: list[RunRecord], random_baseline_loss: float | None = None
) -> StudyResult:
    """Apply the full registered decision procedure to a completed grid.

    `random_baseline_loss` is the loss of an untrained model (ln of vocabulary size). When
    supplied it enables the registered instrument-resolution check: if the margin is a
    large fraction of the entire range the baseline traversed, the study cannot resolve
    anything and is a design failure rather than a null.
    """
    by_condition: dict[str, list[RunRecord]] = {}
    for record in records:
        by_condition.setdefault(record.condition, []).append(record)

    losses = {c: [r.final_eval_loss for r in rs] for c, rs in by_condition.items()}

    failures = _mechanical_failures(records)
    for required in (BASELINE, PRIMARY_EARLY, PRIMARY_LATE):
        if len(losses.get(required, [])) < 2:
            failures.append(f"condition {required} has fewer than two completed runs")
    if failures:
        return StudyResult(
            verdict=DESIGN_FAILURE,
            reasons=tuple(failures),
            margin=math.nan,
            baseline_mean=math.nan,
            baseline_sd=math.nan,
            primary_delta=math.nan,
            primary_p_value=math.nan,
            primary_mde=math.nan,
            cells=(),
        )

    baseline = losses[BASELINE]
    baseline_mean = fmean(baseline)
    baseline_sd = stdev(baseline)
    margin = registered_margin(baseline)

    cells = tuple(
        cell_verdict(condition, values, baseline, margin)
        for condition, values in sorted(losses.items())
        if condition != BASELINE
    )

    primary_delta = fmean(losses[PRIMARY_EARLY]) - fmean(losses[PRIMARY_LATE])
    primary_p = exact_permutation_p(losses[PRIMARY_EARLY], losses[PRIMARY_LATE])
    primary_mde = minimum_detectable_effect(
        losses[PRIMARY_EARLY], losses[PRIMARY_LATE], margin
    )

    reasons: list[str] = []

    if random_baseline_loss is not None:
        learned_range = random_baseline_loss - baseline_mean
        if learned_range <= 0 or margin > 0.10 * learned_range:
            return StudyResult(
                verdict=DESIGN_FAILURE,
                reasons=(
                    f"margin {margin:.4f} exceeds 10% of the learned range "
                    f"{learned_range:.4f}; the instrument cannot resolve the effect",
                ),
                margin=margin,
                baseline_mean=baseline_mean,
                baseline_sd=baseline_sd,
                primary_delta=primary_delta,
                primary_p_value=primary_p,
                primary_mde=primary_mde,
                cells=cells,
            )

    scarred_controls = [
        cell
        for cell in cells
        if cell.condition.startswith(NEGATIVE_CONTROL_PREFIX) and cell.verdict == SCAR
    ]
    if scarred_controls:
        return StudyResult(
            verdict=DESIGN_FAILURE,
            reasons=tuple(
                f"negative control {cell.condition} scarred "
                f"(delta {cell.delta:.4f}, p {cell.p_value:.4f})"
                for cell in scarred_controls
            ),
            margin=margin,
            baseline_mean=baseline_mean,
            baseline_sd=baseline_sd,
            primary_delta=primary_delta,
            primary_p_value=primary_p,
            primary_mde=primary_mde,
            cells=cells,
        )

    early_cell = next(cell for cell in cells if cell.condition == PRIMARY_EARLY)

    if (
        early_cell.verdict == SCAR
        and primary_p <= ALPHA
        and primary_delta >= margin
    ):
        verdict = CRITICAL_PERIOD
        reasons.append(
            f"{PRIMARY_EARLY} scarred and exceeded {PRIMARY_LATE} by "
            f"{primary_delta:.4f} nats (p {primary_p:.4f})"
        )
    elif primary_p > ALPHA and primary_mde <= margin:
        verdict = NO_CRITICAL_PERIOD
        reasons.append(
            f"primary contrast did not reject (p {primary_p:.4f}) at a resolution "
            f"(MDE {primary_mde:.4f}) at or below the margin {margin:.4f}"
        )
    else:
        verdict = INCONCLUSIVE
        if early_cell.verdict != SCAR:
            reasons.append(f"{PRIMARY_EARLY} returned {early_cell.verdict}, not {SCAR}")
        if primary_p > ALPHA:
            reasons.append(
                f"primary contrast did not reject (p {primary_p:.4f}) but MDE "
                f"{primary_mde:.4f} exceeds the margin {margin:.4f}"
            )
        elif primary_delta < margin:
            reasons.append(
                f"primary delta {primary_delta:.4f} is below the margin {margin:.4f}"
            )

    return StudyResult(
        verdict=verdict,
        reasons=tuple(reasons),
        margin=margin,
        baseline_mean=baseline_mean,
        baseline_sd=baseline_sd,
        primary_delta=primary_delta,
        primary_p_value=primary_p,
        primary_mde=primary_mde,
        cells=cells,
    )

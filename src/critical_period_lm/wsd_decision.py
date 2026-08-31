"""Draft decision rules for the v6 onset study. **Not registered, not frozen.**

The v5 rules are frozen and stay that way; this is a separate module because v6 asks a
different question and must not inherit v5's credit. What it *does* inherit, unchanged and by
import, is every primitive v5 rehearsed: `exact_permutation_p`, `fit_exponent`, `paired_gaps`,
`t_interval`, `level_margin`. Only the verdict is new, and a new verdict earns nothing until
it has returned each of its outcomes correctly against fabricated ladders with planted onset
curves. That is `tests/test_wsd_decision.py`.

## The question

v5 measured that damage from a later deficit is repaired more slowly. Under v5's cosine
schedule a later onset is also a *lower learning rate*, so that result is a statement about
one confounded axis. The WSD trunk holds the rate constant across a 35x span of training time,
so v6 asks the separated question:

    does the repair exponent depend on onset when the learning rate does not change?

- **It does** -> onset is doing work of its own, and v5's effect is not merely schedule
  position.
- **It does not** -> the honest reading is that v5's effect was the schedule, and the paper's
  limitation about the confound becomes its result.

## Two readings, because one pairwise contrast has a blind spot

The primary is a contrast between the earliest and latest rate-matched onsets. That is exact,
uses v5's machinery, and is the whole test **if the onset curve is monotonic**. It is blind to
a curve that dips in the middle and returns — which is exactly the shape Achille et al. report
in vision, so the blind spot is not hypothetical here.

So a second reading is registered alongside it: **do the seeds agree on an ordering of the
onsets?** Under a null where onset does nothing, each seed's ranking of the onsets is its own
noise and agreement is chance. Concordance is therefore evidence of structure whatever its
shape. When the pairwise says flat and the concordance says the seeds agree, the verdict is
`INCONCLUSIVE` rather than a null — the guard is registered rather than discovered afterwards.

Both readings are reported always. Neither may be swapped for the other after the fact.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import fmean, stdev

from .decision_rules import (
    ALPHA,
    EXPONENT_MARGIN_FLOOR,
    EXPONENT_MARGIN_SD_MULTIPLE,
    RunRecord,
    exact_permutation_p,
    fit_exponent,
    paired_gaps,
    t_interval,
)

# --- Draft constants. Not registered. -------------------------------------------------

BASELINE = "baseline"
CONTROL_PREFIX = "fixed_"
DEFICIT_PREFIX = "shuffle_"

#: Concordance is called meaningful below this p-value. Separate from ALPHA because it guards
#: a null rather than supporting a claim, and a guard should trip easily.
CONCORDANCE_ALPHA = 0.05

#: Draws for the concordance randomisation. Unlike every other test in this project this one
#: is not exact -- (k!)^n assignments cannot be enumerated -- and the docstring says so rather
#: than letting the word "permutation" imply exactness it does not have.
CONCORDANCE_DRAWS = 20_000

#: Fixed so the randomisation is reproducible. The draws come from the null and do not
#: depend on the data, so a constant seed costs nothing.
CONCORDANCE_SEED = 6

ONSET_EFFECT = "ONSET_EFFECT_AT_CONSTANT_RATE"
NO_ONSET_EFFECT = "NO_ONSET_EFFECT_AT_CONSTANT_RATE"
CONTROL_ONSET_DEPENDENT = "CONTROL_ONSET_DEPENDENT"
ARM_DID_NOT_DECAY = "ARM_DID_NOT_DECAY"
INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class OnsetFit:
    condition: str
    onset: int
    rate_matched: bool
    alpha: float
    alpha_low: float
    alpha_high: float
    per_seed_alpha: tuple[float, ...]


@dataclass(frozen=True)
class OnsetResult:
    verdict: str
    reasons: tuple[str, ...]
    margin: float
    primary_delta: float
    primary_p: float
    concordance: float
    concordance_p: float
    fits: tuple[OnsetFit, ...]


def per_seed_exponents(gaps: dict[int, dict[int, float]]) -> dict[int, float]:
    """One exponent per seed, from that seed's own gaps across budgets."""
    budgets = sorted(gaps)
    seeds = sorted(set.intersection(*(set(gaps[b]) for b in budgets)))
    return {s: fit_exponent(budgets, [gaps[b][s] for b in budgets]) for s in seeds}


def margin_from(control_alphas: list[float]) -> float:
    """Three times the control's own per-seed scatter, floored. v5's rule, unchanged."""
    if len(control_alphas) < 2:
        return EXPONENT_MARGIN_FLOOR
    return max(
        EXPONENT_MARGIN_SD_MULTIPLE * stdev(control_alphas), EXPONENT_MARGIN_FLOOR
    )


def kendall_w(rankings: list[list[int]]) -> float:
    """Agreement among seeds about the ordering of onsets, on [0, 1].

    `rankings[i][j]` is the rank seed `i` gives onset `j`. 0 is no agreement beyond chance,
    1 is every seed ordering the onsets identically. Unlike a pairwise contrast this notices
    a curve that dips and returns.
    """
    n, k = len(rankings), len(rankings[0])
    if n < 2 or k < 2:
        return 0.0
    totals = [sum(row[j] for row in rankings) for j in range(k)]
    mean_total = fmean(totals)
    spread = math.fsum((t - mean_total) ** 2 for t in totals)
    return 12.0 * spread / (n**2 * (k**3 - k))


def _rank(values: list[float]) -> list[float]:
    """Ranks, with ties sharing their average.

    Breaking ties by position would make every seed rank an exactly flat curve identically,
    which reads as perfect agreement about nothing. Averaging ties sends that case to zero
    concordance, which is what it is.
    """
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        stop = start
        while stop + 1 < len(order) and values[order[stop + 1]] == values[order[start]]:
            stop += 1
        shared = fmean(range(start + 1, stop + 2))
        for index in order[start : stop + 1]:
            ranks[index] = shared
        start = stop + 1
    return ranks


def concordance_p(rankings: list[list[int]], draws: int = CONCORDANCE_DRAWS) -> float:
    """How often independent random orderings agree at least as much as the observed ones.

    **This is a randomisation test, not an exact one**, and it is the only test in this
    project that is not. The null space is `(k!)^n` assignments — 120^8 at five onsets and
    eight seeds — so it is sampled rather than enumerated. The sampler runs from a fixed seed
    so the value is reproducible, and the `+1` in numerator and denominator keeps it from
    ever reaching zero.
    """
    observed = kendall_w(rankings)
    n, k = len(rankings), len(rankings[0])
    identity = list(range(1, k + 1))

    rng = random.Random(CONCORDANCE_SEED)
    extreme = 0
    for _ in range(draws):
        shuffled = []
        for _ in range(n):
            row = identity[:]
            rng.shuffle(row)
            shuffled.append(row)
        if kendall_w(shuffled) >= observed:
            extreme += 1
    return (extreme + 1) / (draws + 1)


def onset_of(condition: str) -> int:
    """`shuffle_600` -> 600. The onset is carried in the condition name, as in v5."""
    return int(condition.rsplit("_", 1)[-1])


def fit_all(records: list[RunRecord], matched: set[int]) -> list[OnsetFit]:
    gaps = paired_gaps(records)
    fits = []
    for condition in sorted(gaps, key=lambda c: (c.split("_")[0], onset_of(c))):
        by_budget = {b: dict(gaps[condition][b]) for b in gaps[condition]}
        per_seed = per_seed_exponents(by_budget)
        values = [per_seed[s] for s in sorted(per_seed)]
        _, low, high = t_interval(values)
        onset = onset_of(condition)
        fits.append(
            OnsetFit(condition, onset, onset in matched, fmean(values), low, high, tuple(values))
        )
    return fits


def study_verdict(records: list[RunRecord], matched: set[int]) -> OnsetResult:
    """The registered reading. Pure function of the records; no discretion anywhere."""
    fits = fit_all(records, matched)
    controls = [f for f in fits if f.condition.startswith(CONTROL_PREFIX)]
    arms = [f for f in fits if f.condition.startswith(DEFICIT_PREFIX) and f.rate_matched]
    reasons: list[str] = []

    if not controls:
        return OnsetResult(INCONCLUSIVE, ("no control arm",), EXPONENT_MARGIN_FLOOR,
                           0.0, 1.0, 0.0, 1.0, tuple(fits))
    margin = margin_from(list(controls[0].per_seed_alpha))

    # Gate 1: the control must not itself move with onset, or the axis is not clean.
    if len(controls) >= 2:
        spread = max(f.alpha for f in controls) - min(f.alpha for f in controls)
        if spread >= margin:
            reasons.append(
                f"control exponent varies with onset by {spread:.3f}, at or above the "
                f"margin {margin:.3f}: the onset axis is confounded"
            )
            return OnsetResult(CONTROL_ONSET_DEPENDENT, tuple(reasons), margin,
                               0.0, 1.0, 0.0, 1.0, tuple(fits))

    # Gate 2: an arm whose gap does not decay measures "no time to recover", not slow repair.
    flat = [f.condition for f in arms if abs(f.alpha) < margin]
    if flat:
        reasons.append(f"no decay in {', '.join(flat)}: exponent within the margin of zero")
        return OnsetResult(ARM_DID_NOT_DECAY, tuple(reasons), margin,
                           0.0, 1.0, 0.0, 1.0, tuple(fits))

    if len(arms) < 2:
        return OnsetResult(INCONCLUSIVE, ("fewer than two rate-matched arms",), margin,
                           0.0, 1.0, 0.0, 1.0, tuple(fits))

    earliest, latest = min(arms, key=lambda f: f.onset), max(arms, key=lambda f: f.onset)
    delta = earliest.alpha - latest.alpha
    p_value = exact_permutation_p(
        list(earliest.per_seed_alpha), list(latest.per_seed_alpha), two_sided=True
    )

    seeds = min(len(f.per_seed_alpha) for f in arms)
    rankings = [_rank([f.per_seed_alpha[i] for f in arms]) for i in range(seeds)]
    concordance = kendall_w(rankings)
    conc_p = concordance_p(rankings)

    if abs(delta) >= margin and p_value <= ALPHA:
        reasons.append(
            f"exponent differs by {abs(delta):.3f} between onsets {earliest.onset} and "
            f"{latest.onset} at one learning rate (margin {margin:.3f}, p {p_value:.4f})"
        )
        verdict = ONSET_EFFECT
    elif abs(delta) < margin and p_value > ALPHA:
        # The guard needs a magnitude as well as agreement. Concordance alone detects any
        # consistent structure however small, so on a flat curve a systematic difference of
        # 1e-9 would block the null forever. The blind spot it exists to close is specific:
        # the extremes match while some interior onset differs by more than the margin.
        spread = max(f.alpha for f in arms) - min(f.alpha for f in arms)
        if spread >= margin and conc_p <= CONCORDANCE_ALPHA:
            reasons.append(
                f"the extreme pair is flat, but the arms span {spread:.3f} (at or above the "
                f"margin {margin:.3f}) and seeds agree on their ordering (W {concordance:.3f}, "
                f"p {conc_p:.4f}); a non-monotonic curve the primary contrast cannot see is "
                f"not ruled out"
            )
            verdict = INCONCLUSIVE
        else:
            reasons.append(
                f"exponent does not vary with onset at one learning rate "
                f"(delta {abs(delta):.3f} < margin {margin:.3f}, p {p_value:.4f}, "
                f"W {concordance:.3f})"
            )
            verdict = NO_ONSET_EFFECT
    else:
        reasons.append(
            f"margin and significance disagree: delta {abs(delta):.3f} against margin "
            f"{margin:.3f}, p {p_value:.4f}"
        )
        verdict = INCONCLUSIVE

    return OnsetResult(verdict, tuple(reasons), margin, delta, p_value,
                       concordance, conc_p, tuple(fits))

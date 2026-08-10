# The control replaces the theoretical anchor, and the absolute question is dropped

**Date:** 2026-08-10
**Design version:** v3-draft to v4
**Decided:** after reading ladder 2, and because of it
**Pre-freeze:** yes. This is the last change before the freeze.

## What changed

Two things, and the second matters more.

**Readings are taken against the control.** `LAG` / `SUBLINEAR` / `PERSISTENT`, which
compared `alpha` with the theoretical values 1 and 0, become `LIKE_CONTROL` /
`SLOWER_THAN_CONTROL` / `FASTER_THAN_CONTROL`, which compare it with the control's own
fitted exponent. A control far from 1 is no longer a design failure; it is the anchor.

**The absolute question is dropped.** Whether damage is a lag or a scar is declared out of
scope in Section 3.2.1, and `CLAIMS.md` forbids using any exponent to answer it.

## Why

Ladder 2 returned `DESIGN_FAILURE` because the control's exponent interval,
1.139 [1.015, 1.262], excluded 1 by 0.015. The gate was wrong, not the control.

`gap = b(T)·Δ/T`, so `alpha = 1` is the pure-lag prediction **only if the baseline curve's
log-slope `b` is constant**. Measured on ladder 2's baseline rungs:

| Interval | `b` |
| --- | --- |
| 2,700 → 5,400 | 0.3688 |
| 5,400 → 10,800 | 0.2586 |

A 30% fall per doubling. Correcting the derivation puts the pure-lag anchor near 1.26–1.51
depending on how the slopes are combined. Under 1.000 the control reads too fast; under the
corrected value it reads too slow. **Two incompatible readings of one number, decided
entirely by an assumption made outside the experiment** — which is the signal that the
anchor should not be theoretical.

`b(T)` is common to every condition at a rung. It cancels in a comparison and cancels
nowhere else, so the control is the only sound reference available.

## Why the absolute question had to go with it

The physically meaningful quantity is `Δ_eff`, the deficit's cost in effective training
steps; a pure lag is exactly `Δ_eff` constant across rungs, and that statement needs no
assumption about curve shape. Computing it means inverting the baseline curve. Ladder 2:

| Condition | 2,700 | 5,400 | 10,800 |
| --- | --- | --- | --- |
| `fixed_early_N4` | 1370 | 693 | 882 |
| `shuffle_early_N4` | 1327 | 652 | 807 |
| `shuffle_late_N4` | 1135 | 520 | 890 |

Non-monotonic in every condition — an artefact of interpolating between exactly three
points. A two-parameter log fit to three rungs has one residual degree of freedom and a
slope the data show is not constant; a three-parameter fit has none. **Three rungs cannot
estimate `Δ_eff`**, so the absolute question is not answerable at this ladder resolution and
is dropped rather than dressed up.

## What survives, and what was checked

The primary contrast never depended on the anchor: `alpha(early) − alpha(late) = +0.392`,
two-sided p = 0.0079, and `shuffle_early` sits on the control (+0.023, p = 0.87) while
`shuffle_late` does not (−0.369, p = 0.0079).

The obvious alternative — a common additive floor making the higher-starting condition look
steeper by arithmetic — was tested and refuted. The spread of the three exponents is
*minimised* at floor 0 and grows monotonically as any floor is subtracted:

| Floor subtracted | Spread of the three exponents |
| --- | --- |
| 0.000 | 0.378 |
| 0.008 | 0.457 |
| 0.016 | 0.686 |

A floor artefact would collapse the spread at some plausible floor. It does the opposite.

## Why this is the last revision

This is the fourth endpoint. The first three each smuggled a parameter in from outside the
experiment: where the run happened to stop, an arbitrary 0.01-nat floor, and a theoretical
`alpha = 1`. A control-anchored comparison smuggles in nothing — every quantity it uses is
measured in the same runs. That is a difference in kind and it is the natural stopping
point.

The remaining known weaknesses are recorded as limitations rather than fixed: the t-interval
on `alpha` at five seeds, the power law fitted over a 4× range, and the top-rung precision
limit where the gap is only about five times the baseline seed SD.

## Sensitivity note, post-hoc and labelled

Baseline seed 4 at 10,800 was the worst of five, compressing gaps at that seed and producing
exponent outliers of 1.300 and 1.582. Dropping seed 4 entirely: control 1.098, early 1.057,
late 0.773; early − late +0.284 at p = 0.0286. Every conclusion survives. **No seed is
excluded from any reported analysis**; this is a robustness note only.

## The registered run uses fresh seeds

Calibration used seeds 0–4; the registered ladder uses 5–9. Reusing them would make the
registered run a recomputation rather than a replication, and the freeze would be
ceremonial. Section 8.3.

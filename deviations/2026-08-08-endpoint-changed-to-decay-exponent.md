# Endpoint changed from a categorical ladder verdict to an estimated decay exponent

**Date:** 2026-08-08
**Design version:** v2-draft to v3-draft
**Decided:** after reading ladder 1, and because of it
**Pre-freeze:** yes. Nothing was frozen; no registered run exists.

## What changed

The endpoint was a four-way categorical verdict on whether a condition's gap had fallen
below a fixed 0.01-nat floor by the top rung. It is now an estimate: the gap is fitted as
`gap(T) = c / T^alpha` per seed, and `alpha` with its interval is the reported quantity.

## Why

Two reasons, both from ladder 1.

**The categorical endpoint went blind where the conditions converged.** At the top rung the
early and late arms differed by +0.0003 nats at p = 0.50 — nothing at all — while their
decay exponents differed by 0.276. All three conditions had converged in *level* (0.0229,
0.0221, 0.0218) while still differing in *rate*. A verdict on level could not see it.

**Every categorical outcome hinged on a number we chose.** With gaps decaying as a power law
nothing is ever exactly zero, so `TRANSIENT` versus `PERSISTENT` was a statement about
budget against an arbitrary floor. The exponent has a reading that does not depend on any
threshold: 1 is exactly what lost training alone predicts, 0 is no decay at all.

## What the exponent buys

| Condition (ladder 1, exploratory) | alpha | interval | reading |
| --- | --- | --- | --- |
| `fixed_early_N4` | 1.110 | [0.983, 1.237] | LAG |
| `shuffle_early_N4` | 1.057 | [0.780, 1.334] | LAG |
| `shuffle_late_N4` | 0.781 | [0.728, 0.833] | SUBLINEAR |

The control lands on 1, which is what the design predicts of it and is the first time any
control has behaved. The late arm's interval excludes 1.

## Consequences applied

- Seeds are the replication unit; the interval on `alpha` is a t-interval across seeds. That
  is a normality assumption at five seeds and is declared in Section 5.3 rather than buried.
- The primary contrast is an exact permutation test over per-seed exponents, one-sided in
  the critical-period direction, with a secondary two-sided test.
- A new verdict `REVERSE_ONSET_EFFECT` names late damage outlasting early damage. Its
  provenance is recorded in `CLAIMS.md` C4: ladder 1 motivated the name.
- The exponent margin is self-calibrating from the control's own seed spread, replacing the
  fixed nat floor. The floor survives only to decide whether a condition did any damage
  worth modelling.
- The crossing-budget quantity is computed from the power law. The retired log-linear form
  predicted negative gaps one rung beyond the data and understated the crossing roughly
  twofold.
- A seed whose gap is non-positive at any rung is dropped and reported, never nudged into
  the logarithm by an epsilon.

## Seed plan, corrected in the same version

Ladder 1 gave the primary arms four seeds and the baseline three. Gaps are paired by seed,
so the fourth seed of each arm was unpairable at every rung: six runs trained and bought
nothing, and the effective sample fell to three per arm.

That cost exactly the power the data needed. The two-sided exact permutation test has a
smallest attainable p-value fixed by seed count alone — 0.100 at three seeds, 0.029 at four,
0.008 at five. At three seeds it cannot reject at 0.05 whatever the effect size, and ladder
1 duly returned `INCONCLUSIVE` at p = 0.100 on an exponent difference of 0.276 against a
margin of 0.153.

The registered plan is now five seeds for every condition, and the baseline must carry every
seed index any deficit arm uses.

## Status

The rehearsal gate was rerun against the new rules on fabricated ladders with planted
exponents, and the frozen code returns `CRITICAL_PERIOD`, `REVERSE_ONSET_EFFECT`,
`NO_CRITICAL_PERIOD`, `DESIGN_FAILURE` and `INCONCLUSIVE` correctly. No registered run
exists; ladder 1 remains exploratory and cannot support any claim.

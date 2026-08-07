# Warmup changed from a fixed step count to a fraction of the budget

**Date:** 2026-08-06
**Design version:** v1.2-draft to v1.3-draft
**Decided:** after seeing the pilot 2 result, and because of it
**Pre-freeze:** yes.

## What changed

`warmup_steps` was a fixed 500. It is now `WARMUP_FRACTION = 0.02` of `T_total`, computed by
`deficits.warmup_steps` and bound by the freeze corpus.

## Why

Design version v1.2 claimed, in Section 4.1, that a scaled-down run rehearses a full-budget
study rather than truncating one. The argument was that annealing to zero makes convergence a
property of the schedule. That much is true, but it was not sufficient, and the claim was
false as stated:

| | Pilot scale, 5,400 | Full scale, 43,200 |
| --- | --- | --- |
| Warmup as a share of the run | 9.3% | 1.2% |
| Early deficit falling inside warmup | 100% | 16% |
| LR-weighted disturbance, late arm over early | 2.28x | 0.92x |

At pilot scale the entire early deficit sat inside warmup, so "early deficit" meant
"corruption applied while the model was barely learning". The early arm recovered almost
perfectly in pilot 2, and that observation carries much less weight than it appeared to.

Making warmup proportional makes every ratio that defines the treatment scale-invariant, so
the v1.2 claim becomes true rather than merely asserted.

## Consequence for existing runs

Pilots 1 and 2 were run under the fixed-500 warmup and are not comparable to anything
produced after this change. Both are archived under `calibration/archive/`.

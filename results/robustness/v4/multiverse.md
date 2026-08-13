# Specification multiverse — v4

**ROBUSTNESS EXHIBIT. NOT A RESULT.** The registered verdict is whatever the frozen decision code returned; it is reported in `results/registered/` and nothing here revises it. This grid was enumerated after both registered verdicts were known, and exists to show how much of each one rode on a single analysis choice.

**Registered verdict:** `INCONCLUSIVE`
**Frozen specification reproduces it:** yes (`INCONCLUSIVE`, delta +0.438, margin 0.501)

## Verdict across 144 defensible specifications

| Verdict | Specifications | Share |
| --- | --- | --- |
| `INCONCLUSIVE`  ← frozen | 90 | 62% |
| `REVERSE_ONSET_EFFECT` | 54 | 38% |

## Which choice moves the verdict

Share of specifications returning the registered verdict, held at each level.

**scale**

| Level | Agrees with registered | |
| --- | --- | --- |
| `control` ← frozen | 83% | █████████████████ |
| `pooled-all` | 67% | █████████████ |
| `pooled-arms` | 33% | ███████ |
| `mad-control` | 67% | █████████████ |

**multiple**

| Level | Agrees with registered | |
| --- | --- | --- |
| `2.0` | 38% | ████████ |
| `3.0` ← frozen | 62% | ████████████ |
| `4.0` | 88% | ██████████████████ |

**floor**

| Level | Agrees with registered | |
| --- | --- | --- |
| `0.05` | 62% | ████████████ |
| `0.1` ← frozen | 62% | ████████████ |
| `0.2` | 62% | ████████████ |

**estimator**

| Level | Agrees with registered | |
| --- | --- | --- |
| `ols` ← frozen | 62% | ████████████ |
| `theil-sen` | 62% | ████████████ |

**rungs**

| Level | Agrees with registered | |
| --- | --- | --- |
| `all` ← frozen | 33% | ███████ |
| `drop-lowest` | 92% | ██████████████████ |

## Specifications excluded by name, and why

Including options already known to be wrong lets bad pipelines vote.

| Excluded | Reason |
| --- | --- |
| unpaired gaps | discards the seed pairing the design registered; strictly worse, not merely different |
| nudging non-positive gaps into the logarithm | a gap at or below zero is noise around zero, not decay; the frozen fitter refuses it |
| anchoring the exponent on the theoretical value 1 | the design v3 defect, refuted by its own data: the baseline log-slope falls ~30% per doubling, so the pure-lag anchor is not 1 |
| dropping the outlier seed | post-hoc exclusion with no preregistered rule; it is a labelled sensitivity note in STATUS.md, not a defensible specification |

## Every cell

| scale | mult | floor | estimator | rungs | delta | margin | 2-sided p | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| control | 2 | 0.05 | ols | all | +0.438 | 0.334 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.05 | ols | drop-lowest | +0.454 | 0.802 | 0.00794 | `INCONCLUSIVE` |
| control | 2 | 0.05 | theil-sen | all | +0.438 | 0.334 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.05 | theil-sen | drop-lowest | +0.454 | 0.802 | 0.00794 | `INCONCLUSIVE` |
| control | 2 | 0.10 | ols | all | +0.438 | 0.334 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.10 | ols | drop-lowest | +0.454 | 0.802 | 0.00794 | `INCONCLUSIVE` |
| control | 2 | 0.10 | theil-sen | all | +0.438 | 0.334 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.10 | theil-sen | drop-lowest | +0.454 | 0.802 | 0.00794 | `INCONCLUSIVE` |
| control | 2 | 0.20 | ols | all | +0.438 | 0.334 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.20 | ols | drop-lowest | +0.454 | 0.802 | 0.00794 | `INCONCLUSIVE` |
| control | 2 | 0.20 | theil-sen | all | +0.438 | 0.334 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.20 | theil-sen | drop-lowest | +0.454 | 0.802 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.05 | ols | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.05 | ols | drop-lowest | +0.454 | 1.204 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.05 | theil-sen | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.05 | theil-sen | drop-lowest | +0.454 | 1.204 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.10 | ols | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` **←** |
| control | 3 | 0.10 | ols | drop-lowest | +0.454 | 1.204 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.10 | theil-sen | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.10 | theil-sen | drop-lowest | +0.454 | 1.204 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.20 | ols | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.20 | ols | drop-lowest | +0.454 | 1.204 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.20 | theil-sen | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| control | 3 | 0.20 | theil-sen | drop-lowest | +0.454 | 1.204 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.05 | ols | all | +0.438 | 0.668 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.05 | ols | drop-lowest | +0.454 | 1.605 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.05 | theil-sen | all | +0.438 | 0.668 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.05 | theil-sen | drop-lowest | +0.454 | 1.605 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.10 | ols | all | +0.438 | 0.668 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.10 | ols | drop-lowest | +0.454 | 1.605 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.10 | theil-sen | all | +0.438 | 0.668 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.10 | theil-sen | drop-lowest | +0.454 | 1.605 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.20 | ols | all | +0.438 | 0.668 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.20 | ols | drop-lowest | +0.454 | 1.605 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.20 | theil-sen | all | +0.438 | 0.668 | 0.00794 | `INCONCLUSIVE` |
| control | 4 | 0.20 | theil-sen | drop-lowest | +0.454 | 1.605 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 2 | 0.05 | ols | all | +0.438 | 0.222 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.05 | ols | drop-lowest | +0.454 | 0.533 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 2 | 0.05 | theil-sen | all | +0.438 | 0.222 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.05 | theil-sen | drop-lowest | +0.454 | 0.533 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 2 | 0.10 | ols | all | +0.438 | 0.222 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.10 | ols | drop-lowest | +0.454 | 0.533 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 2 | 0.10 | theil-sen | all | +0.438 | 0.222 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.10 | theil-sen | drop-lowest | +0.454 | 0.533 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 2 | 0.20 | ols | all | +0.438 | 0.222 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.20 | ols | drop-lowest | +0.454 | 0.533 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 2 | 0.20 | theil-sen | all | +0.438 | 0.222 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.20 | theil-sen | drop-lowest | +0.454 | 0.533 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 3 | 0.05 | ols | all | +0.438 | 0.332 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.05 | ols | drop-lowest | +0.454 | 0.800 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 3 | 0.05 | theil-sen | all | +0.438 | 0.332 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.05 | theil-sen | drop-lowest | +0.454 | 0.800 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 3 | 0.10 | ols | all | +0.438 | 0.332 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.10 | ols | drop-lowest | +0.454 | 0.800 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 3 | 0.10 | theil-sen | all | +0.438 | 0.332 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.10 | theil-sen | drop-lowest | +0.454 | 0.800 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 3 | 0.20 | ols | all | +0.438 | 0.332 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.20 | ols | drop-lowest | +0.454 | 0.800 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 3 | 0.20 | theil-sen | all | +0.438 | 0.332 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.20 | theil-sen | drop-lowest | +0.454 | 0.800 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.05 | ols | all | +0.438 | 0.443 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.05 | ols | drop-lowest | +0.454 | 1.066 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.05 | theil-sen | all | +0.438 | 0.443 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.05 | theil-sen | drop-lowest | +0.454 | 1.066 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.10 | ols | all | +0.438 | 0.443 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.10 | ols | drop-lowest | +0.454 | 1.066 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.10 | theil-sen | all | +0.438 | 0.443 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.10 | theil-sen | drop-lowest | +0.454 | 1.066 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.20 | ols | all | +0.438 | 0.443 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.20 | ols | drop-lowest | +0.454 | 1.066 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.20 | theil-sen | all | +0.438 | 0.443 | 0.00794 | `INCONCLUSIVE` |
| pooled-all | 4 | 0.20 | theil-sen | drop-lowest | +0.454 | 1.066 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 2 | 0.05 | ols | all | +0.438 | 0.134 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.05 | ols | drop-lowest | +0.454 | 0.323 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.05 | theil-sen | all | +0.438 | 0.134 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.05 | theil-sen | drop-lowest | +0.454 | 0.323 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.10 | ols | all | +0.438 | 0.134 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.10 | ols | drop-lowest | +0.454 | 0.323 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.10 | theil-sen | all | +0.438 | 0.134 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.10 | theil-sen | drop-lowest | +0.454 | 0.323 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.20 | ols | all | +0.438 | 0.200 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.20 | ols | drop-lowest | +0.454 | 0.323 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.20 | theil-sen | all | +0.438 | 0.200 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.20 | theil-sen | drop-lowest | +0.454 | 0.323 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.05 | ols | all | +0.438 | 0.201 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.05 | ols | drop-lowest | +0.454 | 0.484 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 3 | 0.05 | theil-sen | all | +0.438 | 0.201 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.05 | theil-sen | drop-lowest | +0.454 | 0.484 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 3 | 0.10 | ols | all | +0.438 | 0.201 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.10 | ols | drop-lowest | +0.454 | 0.484 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 3 | 0.10 | theil-sen | all | +0.438 | 0.201 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.10 | theil-sen | drop-lowest | +0.454 | 0.484 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 3 | 0.20 | ols | all | +0.438 | 0.201 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.20 | ols | drop-lowest | +0.454 | 0.484 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 3 | 0.20 | theil-sen | all | +0.438 | 0.201 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.20 | theil-sen | drop-lowest | +0.454 | 0.484 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 4 | 0.05 | ols | all | +0.438 | 0.268 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.05 | ols | drop-lowest | +0.454 | 0.646 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 4 | 0.05 | theil-sen | all | +0.438 | 0.268 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.05 | theil-sen | drop-lowest | +0.454 | 0.646 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 4 | 0.10 | ols | all | +0.438 | 0.268 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.10 | ols | drop-lowest | +0.454 | 0.646 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 4 | 0.10 | theil-sen | all | +0.438 | 0.268 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.10 | theil-sen | drop-lowest | +0.454 | 0.646 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 4 | 0.20 | ols | all | +0.438 | 0.268 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.20 | ols | drop-lowest | +0.454 | 0.646 | 0.00794 | `INCONCLUSIVE` |
| pooled-arms | 4 | 0.20 | theil-sen | all | +0.438 | 0.268 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.20 | theil-sen | drop-lowest | +0.454 | 0.646 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 2 | 0.05 | ols | all | +0.438 | 0.251 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.05 | ols | drop-lowest | +0.454 | 0.773 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 2 | 0.05 | theil-sen | all | +0.438 | 0.251 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.05 | theil-sen | drop-lowest | +0.454 | 0.773 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 2 | 0.10 | ols | all | +0.438 | 0.251 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.10 | ols | drop-lowest | +0.454 | 0.773 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 2 | 0.10 | theil-sen | all | +0.438 | 0.251 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.10 | theil-sen | drop-lowest | +0.454 | 0.773 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 2 | 0.20 | ols | all | +0.438 | 0.251 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.20 | ols | drop-lowest | +0.454 | 0.773 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 2 | 0.20 | theil-sen | all | +0.438 | 0.251 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.20 | theil-sen | drop-lowest | +0.454 | 0.773 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 3 | 0.05 | ols | all | +0.438 | 0.376 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.05 | ols | drop-lowest | +0.454 | 1.159 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 3 | 0.05 | theil-sen | all | +0.438 | 0.376 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.05 | theil-sen | drop-lowest | +0.454 | 1.159 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 3 | 0.10 | ols | all | +0.438 | 0.376 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.10 | ols | drop-lowest | +0.454 | 1.159 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 3 | 0.10 | theil-sen | all | +0.438 | 0.376 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.10 | theil-sen | drop-lowest | +0.454 | 1.159 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 3 | 0.20 | ols | all | +0.438 | 0.376 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.20 | ols | drop-lowest | +0.454 | 1.159 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 3 | 0.20 | theil-sen | all | +0.438 | 0.376 | 0.00794 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.20 | theil-sen | drop-lowest | +0.454 | 1.159 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.05 | ols | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.05 | ols | drop-lowest | +0.454 | 1.546 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.05 | theil-sen | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.05 | theil-sen | drop-lowest | +0.454 | 1.546 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.10 | ols | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.10 | ols | drop-lowest | +0.454 | 1.546 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.10 | theil-sen | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.10 | theil-sen | drop-lowest | +0.454 | 1.546 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.20 | ols | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.20 | ols | drop-lowest | +0.454 | 1.546 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.20 | theil-sen | all | +0.438 | 0.501 | 0.00794 | `INCONCLUSIVE` |
| mad-control | 4 | 0.20 | theil-sen | drop-lowest | +0.454 | 1.546 | 0.00794 | `INCONCLUSIVE` |

# Specification multiverse — v5

**ROBUSTNESS EXHIBIT. NOT A RESULT.** The registered verdict is whatever the frozen decision code returned; it is reported in `results/registered/` and nothing here revises it. This grid was enumerated after both registered verdicts were known, and exists to show how much of each one rode on a single analysis choice.

**Registered verdict:** `REVERSE_ONSET_EFFECT`
**Frozen specification reproduces it:** yes (`REVERSE_ONSET_EFFECT`, delta +0.392, margin 0.323)

## Verdict across 144 defensible specifications

| Verdict | Specifications | Share |
| --- | --- | --- |
| `REVERSE_ONSET_EFFECT`  ← frozen | 138 | 96% |
| `INCONCLUSIVE` | 6 | 4% |

## Which choice moves the verdict

Share of specifications returning the registered verdict, held at each level.

**scale**

| Level | Agrees with registered | |
| --- | --- | --- |
| `control` ← frozen | 83% | █████████████████ |
| `pooled-all` | 100% | ████████████████████ |
| `pooled-arms` | 100% | ████████████████████ |
| `mad-control` | 100% | ████████████████████ |

**multiple**

| Level | Agrees with registered | |
| --- | --- | --- |
| `2.0` | 100% | ████████████████████ |
| `3.0` ← frozen | 100% | ████████████████████ |
| `4.0` | 88% | ██████████████████ |

**floor**

| Level | Agrees with registered | |
| --- | --- | --- |
| `0.05` | 96% | ███████████████████ |
| `0.1` ← frozen | 96% | ███████████████████ |
| `0.2` | 96% | ███████████████████ |

**estimator**

| Level | Agrees with registered | |
| --- | --- | --- |
| `ols` ← frozen | 96% | ███████████████████ |
| `theil-sen` | 96% | ███████████████████ |

**rungs**

| Level | Agrees with registered | |
| --- | --- | --- |
| `all` ← frozen | 92% | ██████████████████ |
| `drop-lowest` | 100% | ████████████████████ |

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
| control | 2 | 0.05 | ols | all | +0.392 | 0.216 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.05 | ols | drop-lowest | +0.453 | 0.211 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.05 | theil-sen | all | +0.388 | 0.219 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.211 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.10 | ols | all | +0.392 | 0.216 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.10 | ols | drop-lowest | +0.453 | 0.211 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.10 | theil-sen | all | +0.388 | 0.219 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.211 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.20 | ols | all | +0.392 | 0.216 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.20 | ols | drop-lowest | +0.453 | 0.211 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.20 | theil-sen | all | +0.388 | 0.219 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 2 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.211 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.05 | ols | all | +0.392 | 0.323 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.05 | ols | drop-lowest | +0.453 | 0.317 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.05 | theil-sen | all | +0.388 | 0.328 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.317 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.10 | ols | all | +0.392 | 0.323 | 0.00016 | `REVERSE_ONSET_EFFECT` **←** |
| control | 3 | 0.10 | ols | drop-lowest | +0.453 | 0.317 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.10 | theil-sen | all | +0.388 | 0.328 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.317 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.20 | ols | all | +0.392 | 0.323 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.20 | ols | drop-lowest | +0.453 | 0.317 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.20 | theil-sen | all | +0.388 | 0.328 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 3 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.317 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 4 | 0.05 | ols | all | +0.392 | 0.431 | 0.00016 | `INCONCLUSIVE` |
| control | 4 | 0.05 | ols | drop-lowest | +0.453 | 0.423 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 4 | 0.05 | theil-sen | all | +0.388 | 0.438 | 0.00016 | `INCONCLUSIVE` |
| control | 4 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.423 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 4 | 0.10 | ols | all | +0.392 | 0.431 | 0.00016 | `INCONCLUSIVE` |
| control | 4 | 0.10 | ols | drop-lowest | +0.453 | 0.423 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 4 | 0.10 | theil-sen | all | +0.388 | 0.438 | 0.00016 | `INCONCLUSIVE` |
| control | 4 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.423 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 4 | 0.20 | ols | all | +0.392 | 0.431 | 0.00016 | `INCONCLUSIVE` |
| control | 4 | 0.20 | ols | drop-lowest | +0.453 | 0.423 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| control | 4 | 0.20 | theil-sen | all | +0.388 | 0.438 | 0.00016 | `INCONCLUSIVE` |
| control | 4 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.423 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.05 | ols | all | +0.392 | 0.160 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.05 | ols | drop-lowest | +0.453 | 0.207 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.05 | theil-sen | all | +0.388 | 0.161 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.207 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.10 | ols | all | +0.392 | 0.160 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.10 | ols | drop-lowest | +0.453 | 0.207 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.10 | theil-sen | all | +0.388 | 0.161 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.207 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.20 | ols | all | +0.392 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.20 | ols | drop-lowest | +0.453 | 0.207 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.20 | theil-sen | all | +0.388 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 2 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.207 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.05 | ols | all | +0.392 | 0.240 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.05 | ols | drop-lowest | +0.453 | 0.311 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.05 | theil-sen | all | +0.388 | 0.241 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.311 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.10 | ols | all | +0.392 | 0.240 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.10 | ols | drop-lowest | +0.453 | 0.311 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.10 | theil-sen | all | +0.388 | 0.241 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.311 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.20 | ols | all | +0.392 | 0.240 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.20 | ols | drop-lowest | +0.453 | 0.311 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.20 | theil-sen | all | +0.388 | 0.241 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 3 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.311 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.05 | ols | all | +0.392 | 0.320 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.05 | ols | drop-lowest | +0.453 | 0.414 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.05 | theil-sen | all | +0.388 | 0.322 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.414 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.10 | ols | all | +0.392 | 0.320 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.10 | ols | drop-lowest | +0.453 | 0.414 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.10 | theil-sen | all | +0.388 | 0.322 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.414 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.20 | ols | all | +0.392 | 0.320 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.20 | ols | drop-lowest | +0.453 | 0.414 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.20 | theil-sen | all | +0.388 | 0.322 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-all | 4 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.414 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.05 | ols | all | +0.392 | 0.123 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.05 | ols | drop-lowest | +0.453 | 0.205 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.05 | theil-sen | all | +0.388 | 0.122 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.205 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.10 | ols | all | +0.392 | 0.123 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.10 | ols | drop-lowest | +0.453 | 0.205 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.10 | theil-sen | all | +0.388 | 0.122 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.205 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.20 | ols | all | +0.392 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.20 | ols | drop-lowest | +0.453 | 0.205 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.20 | theil-sen | all | +0.388 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 2 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.205 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.05 | ols | all | +0.392 | 0.184 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.05 | ols | drop-lowest | +0.453 | 0.308 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.05 | theil-sen | all | +0.388 | 0.183 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.308 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.10 | ols | all | +0.392 | 0.184 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.10 | ols | drop-lowest | +0.453 | 0.308 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.10 | theil-sen | all | +0.388 | 0.183 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.308 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.20 | ols | all | +0.392 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.20 | ols | drop-lowest | +0.453 | 0.308 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.20 | theil-sen | all | +0.388 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 3 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.308 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.05 | ols | all | +0.392 | 0.246 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.05 | ols | drop-lowest | +0.453 | 0.410 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.05 | theil-sen | all | +0.388 | 0.244 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.410 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.10 | ols | all | +0.392 | 0.246 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.10 | ols | drop-lowest | +0.453 | 0.410 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.10 | theil-sen | all | +0.388 | 0.244 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.410 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.20 | ols | all | +0.392 | 0.246 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.20 | ols | drop-lowest | +0.453 | 0.410 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.20 | theil-sen | all | +0.388 | 0.244 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| pooled-arms | 4 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.410 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.05 | ols | all | +0.392 | 0.097 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.05 | ols | drop-lowest | +0.453 | 0.100 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.05 | theil-sen | all | +0.388 | 0.166 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.100 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.10 | ols | all | +0.392 | 0.100 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.10 | ols | drop-lowest | +0.453 | 0.100 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.10 | theil-sen | all | +0.388 | 0.166 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.100 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.20 | ols | all | +0.392 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.20 | ols | drop-lowest | +0.453 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.20 | theil-sen | all | +0.388 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 2 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.05 | ols | all | +0.392 | 0.146 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.05 | ols | drop-lowest | +0.453 | 0.151 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.05 | theil-sen | all | +0.388 | 0.250 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.151 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.10 | ols | all | +0.392 | 0.146 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.10 | ols | drop-lowest | +0.453 | 0.151 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.10 | theil-sen | all | +0.388 | 0.250 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.151 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.20 | ols | all | +0.392 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.20 | ols | drop-lowest | +0.453 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.20 | theil-sen | all | +0.388 | 0.250 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 3 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.05 | ols | all | +0.392 | 0.194 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.05 | ols | drop-lowest | +0.453 | 0.201 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.05 | theil-sen | all | +0.388 | 0.333 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.05 | theil-sen | drop-lowest | +0.453 | 0.201 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.10 | ols | all | +0.392 | 0.194 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.10 | ols | drop-lowest | +0.453 | 0.201 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.10 | theil-sen | all | +0.388 | 0.333 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.10 | theil-sen | drop-lowest | +0.453 | 0.201 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.20 | ols | all | +0.392 | 0.200 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.20 | ols | drop-lowest | +0.453 | 0.201 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.20 | theil-sen | all | +0.388 | 0.333 | 0.00016 | `REVERSE_ONSET_EFFECT` |
| mad-control | 4 | 0.20 | theil-sen | drop-lowest | +0.453 | 0.201 | 0.00016 | `REVERSE_ONSET_EFFECT` |

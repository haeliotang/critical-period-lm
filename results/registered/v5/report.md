# Study report

**Verdict:** `REVERSE_ONSET_EFFECT`

## Basis

- onset mattered in the direction opposite to a critical period: shuffle_late_N4 repaired more slowly than shuffle_early_N4 by 0.392 in exponent (two-sided p 0.0002). Late damage outlasts early damage, which no critical-period account predicts
- shuffle_early_N4 read LIKE_CONTROL: early damage is repaired at the same rate as the information-preserving control

## How fast is the damage repaired?

Gap to baseline, paired by seed, fitted as `gap(T) = c / T^alpha`. Each seed is
fitted separately and the interval is across seeds.

**Every reading is taken against the negative control, not against a theoretical
value.** `alpha` mixes the deficit's cost with the baseline curve's own shape, and
that shape is common to every condition at a rung, so it cancels in a comparison and
nowhere else. What this buys is a comparative answer; what it gives up is the
absolute one — whether damage is a lag or a scar is out of scope, see `CLAIMS.md`.

| Condition | 1,350 | 2,700 | 5,400 | 10,800 | alpha | 95% interval | vs control | p | reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fixed_early_N4` | +0.2106 | +0.1030 | +0.0434 | +0.0197 | 1.158 | [1.068, 1.248] | anchor | — | ANCHOR (the reference every other condition is read against) |
| `shuffle_early_N4` | +0.2091 | +0.1019 | +0.0467 | +0.0190 | 1.155 | [1.085, 1.225] | -0.003 | 0.9524 | LIKE_CONTROL (repairs at the control's rate) |
| `shuffle_late_N4` | +0.1097 | +0.0643 | +0.0381 | +0.0224 | 0.763 | [0.744, 0.782] | -0.395 | 0.0002 | SLOWER_THAN_CONTROL (repairs more slowly than the control) |

### Descriptive only: what a pure lag would have predicted

Reported so a reader can see the assumption fail rather than take it on trust.
Neither number gates anything.

- Baseline local log-slopes between rungs: 0.4861, 0.3655, 0.2646
- Naive pure-lag exponent, valid only if those slopes are equal: 1.000
- Corrected for how they actually move: 1.585

The correction rests on a handful of slope estimates from a handful of points. It is
enough to show that an anchor of 1 is wrong; it is not enough to be an anchor.

## Instrument

- Top budget: 10,800 steps
- Baseline seed SD at the top budget: 0.0023
- Level floor (is there damage to model): 0.0100 nats
- Exponent margin (from the control's own seed spread): 0.323

## Primary contrast: does onset change the decay rate?

A critical period predicts early damage is the harder to repair, so it should decay
*more slowly*: `alpha_early < alpha_late`. The one-sided test is that prediction.
The two-sided test exists so that an onset effect running the other way is reported
rather than absorbed into a null.

- alpha(early) − alpha(late): +0.392
- One-sided p, critical-period direction: 1.0000
- Two-sided p, onset matters either way: 0.0002

## Per-seed exponents

| Condition | seeds fitted | seeds dropped | per-seed alpha |
| --- | --- | --- | --- |
| `fixed_early_N4` | 8 | 0 | 1.165, 1.263, 1.140, 1.121, 0.942, 1.186, 1.144, 1.302 |
| `shuffle_early_N4` | 8 | 0 | 1.073, 1.270, 1.204, 1.064, 1.075, 1.245, 1.108, 1.199 |
| `shuffle_late_N4` | 8 | 0 | 0.776, 0.756, 0.759, 0.776, 0.763, 0.803, 0.735, 0.737 |

## Runs dropped for want of a baseline partner

None. Every deficit run had a baseline partner at its budget and seed.

## Runs included

Every run record found was included. There is no exclusion rule.

| Condition | Budget | Seed | Final eval loss |
| --- | --- | --- | --- |
| `baseline` | 1,350 | 10 | 2.6453 |
| `baseline` | 1,350 | 11 | 2.6168 |
| `baseline` | 1,350 | 12 | 2.6259 |
| `baseline` | 1,350 | 13 | 2.6364 |
| `baseline` | 1,350 | 14 | 2.6362 |
| `baseline` | 1,350 | 15 | 2.6400 |
| `baseline` | 1,350 | 16 | 2.6319 |
| `baseline` | 1,350 | 17 | 2.6211 |
| `baseline` | 2,700 | 10 | 2.3048 |
| `baseline` | 2,700 | 11 | 2.2964 |
| `baseline` | 2,700 | 12 | 2.2821 |
| `baseline` | 2,700 | 13 | 2.2908 |
| `baseline` | 2,700 | 14 | 2.2939 |
| `baseline` | 2,700 | 15 | 2.2876 |
| `baseline` | 2,700 | 16 | 2.3020 |
| `baseline` | 2,700 | 17 | 2.3005 |
| `baseline` | 5,400 | 10 | 2.0442 |
| `baseline` | 5,400 | 11 | 2.0519 |
| `baseline` | 5,400 | 12 | 2.0417 |
| `baseline` | 5,400 | 13 | 2.0336 |
| `baseline` | 5,400 | 14 | 2.0340 |
| `baseline` | 5,400 | 15 | 2.0360 |
| `baseline` | 5,400 | 16 | 2.0440 |
| `baseline` | 5,400 | 17 | 2.0460 |
| `baseline` | 10,800 | 10 | 1.8588 |
| `baseline` | 10,800 | 11 | 1.8587 |
| `baseline` | 10,800 | 12 | 1.8592 |
| `baseline` | 10,800 | 13 | 1.8543 |
| `baseline` | 10,800 | 14 | 1.8543 |
| `baseline` | 10,800 | 15 | 1.8585 |
| `baseline` | 10,800 | 16 | 1.8598 |
| `baseline` | 10,800 | 17 | 1.8602 |
| `fixed_early_N4` | 1,350 | 10 | 2.8482 |
| `fixed_early_N4` | 1,350 | 11 | 2.8459 |
| `fixed_early_N4` | 1,350 | 12 | 2.8385 |
| `fixed_early_N4` | 1,350 | 13 | 2.8446 |
| `fixed_early_N4` | 1,350 | 14 | 2.8287 |
| `fixed_early_N4` | 1,350 | 15 | 2.8565 |
| `fixed_early_N4` | 1,350 | 16 | 2.8276 |
| `fixed_early_N4` | 1,350 | 17 | 2.8483 |
| `fixed_early_N4` | 2,700 | 10 | 2.4039 |
| `fixed_early_N4` | 2,700 | 11 | 2.4023 |
| `fixed_early_N4` | 2,700 | 12 | 2.3866 |
| `fixed_early_N4` | 2,700 | 13 | 2.3938 |
| `fixed_early_N4` | 2,700 | 14 | 2.3966 |
| `fixed_early_N4` | 2,700 | 15 | 2.4032 |
| `fixed_early_N4` | 2,700 | 16 | 2.3999 |
| `fixed_early_N4` | 2,700 | 17 | 2.3958 |
| `fixed_early_N4` | 5,400 | 10 | 2.0860 |
| `fixed_early_N4` | 5,400 | 11 | 2.0792 |
| `fixed_early_N4` | 5,400 | 12 | 2.0884 |
| `fixed_early_N4` | 5,400 | 13 | 2.0819 |
| `fixed_early_N4` | 5,400 | 14 | 2.0887 |
| `fixed_early_N4` | 5,400 | 15 | 2.0829 |
| `fixed_early_N4` | 5,400 | 16 | 2.0913 |
| `fixed_early_N4` | 5,400 | 17 | 2.0799 |
| `fixed_early_N4` | 10,800 | 10 | 1.8772 |
| `fixed_early_N4` | 10,800 | 11 | 1.8781 |
| `fixed_early_N4` | 10,800 | 12 | 1.8792 |
| `fixed_early_N4` | 10,800 | 13 | 1.8744 |
| `fixed_early_N4` | 10,800 | 14 | 1.8813 |
| `fixed_early_N4` | 10,800 | 15 | 1.8774 |
| `fixed_early_N4` | 10,800 | 16 | 1.8776 |
| `fixed_early_N4` | 10,800 | 17 | 1.8760 |
| `shuffle_early_N4` | 1,350 | 10 | 2.8542 |
| `shuffle_early_N4` | 1,350 | 11 | 2.8336 |
| `shuffle_early_N4` | 1,350 | 12 | 2.8326 |
| `shuffle_early_N4` | 1,350 | 13 | 2.8281 |
| `shuffle_early_N4` | 1,350 | 14 | 2.8593 |
| `shuffle_early_N4` | 1,350 | 15 | 2.8581 |
| `shuffle_early_N4` | 1,350 | 16 | 2.8301 |
| `shuffle_early_N4` | 1,350 | 17 | 2.8305 |
| `shuffle_early_N4` | 2,700 | 10 | 2.3953 |
| `shuffle_early_N4` | 2,700 | 11 | 2.4015 |
| `shuffle_early_N4` | 2,700 | 12 | 2.3932 |
| `shuffle_early_N4` | 2,700 | 13 | 2.3855 |
| `shuffle_early_N4` | 2,700 | 14 | 2.3993 |
| `shuffle_early_N4` | 2,700 | 15 | 2.4029 |
| `shuffle_early_N4` | 2,700 | 16 | 2.3945 |
| `shuffle_early_N4` | 2,700 | 17 | 2.4008 |
| `shuffle_early_N4` | 5,400 | 10 | 2.0902 |
| `shuffle_early_N4` | 5,400 | 11 | 2.0837 |
| `shuffle_early_N4` | 5,400 | 12 | 2.0869 |
| `shuffle_early_N4` | 5,400 | 13 | 2.0888 |
| `shuffle_early_N4` | 5,400 | 14 | 2.0909 |
| `shuffle_early_N4` | 5,400 | 15 | 2.0862 |
| `shuffle_early_N4` | 5,400 | 16 | 2.0850 |
| `shuffle_early_N4` | 5,400 | 17 | 2.0932 |
| `shuffle_early_N4` | 10,800 | 10 | 1.8808 |
| `shuffle_early_N4` | 10,800 | 11 | 1.8758 |
| `shuffle_early_N4` | 10,800 | 12 | 1.8766 |
| `shuffle_early_N4` | 10,800 | 13 | 1.8739 |
| `shuffle_early_N4` | 10,800 | 14 | 1.8772 |
| `shuffle_early_N4` | 10,800 | 15 | 1.8748 |
| `shuffle_early_N4` | 10,800 | 16 | 1.8799 |
| `shuffle_early_N4` | 10,800 | 17 | 1.8771 |
| `shuffle_late_N4` | 1,350 | 10 | 2.7619 |
| `shuffle_late_N4` | 1,350 | 11 | 2.7258 |
| `shuffle_late_N4` | 1,350 | 12 | 2.7333 |
| `shuffle_late_N4` | 1,350 | 13 | 2.7461 |
| `shuffle_late_N4` | 1,350 | 14 | 2.7450 |
| `shuffle_late_N4` | 1,350 | 15 | 2.7558 |
| `shuffle_late_N4` | 1,350 | 16 | 2.7390 |
| `shuffle_late_N4` | 1,350 | 17 | 2.7242 |
| `shuffle_late_N4` | 2,700 | 10 | 2.3681 |
| `shuffle_late_N4` | 2,700 | 11 | 2.3587 |
| `shuffle_late_N4` | 2,700 | 12 | 2.3502 |
| `shuffle_late_N4` | 2,700 | 13 | 2.3567 |
| `shuffle_late_N4` | 2,700 | 14 | 2.3576 |
| `shuffle_late_N4` | 2,700 | 15 | 2.3541 |
| `shuffle_late_N4` | 2,700 | 16 | 2.3647 |
| `shuffle_late_N4` | 2,700 | 17 | 2.3627 |
| `shuffle_late_N4` | 5,400 | 10 | 2.0827 |
| `shuffle_late_N4` | 5,400 | 11 | 2.0895 |
| `shuffle_late_N4` | 5,400 | 12 | 2.0808 |
| `shuffle_late_N4` | 5,400 | 13 | 2.0718 |
| `shuffle_late_N4` | 5,400 | 14 | 2.0717 |
| `shuffle_late_N4` | 5,400 | 15 | 2.0739 |
| `shuffle_late_N4` | 5,400 | 16 | 2.0823 |
| `shuffle_late_N4` | 5,400 | 17 | 2.0835 |
| `shuffle_late_N4` | 10,800 | 10 | 1.8817 |
| `shuffle_late_N4` | 10,800 | 11 | 1.8812 |
| `shuffle_late_N4` | 10,800 | 12 | 1.8817 |
| `shuffle_late_N4` | 10,800 | 13 | 1.8762 |
| `shuffle_late_N4` | 10,800 | 14 | 1.8766 |
| `shuffle_late_N4` | 10,800 | 15 | 1.8804 |
| `shuffle_late_N4` | 10,800 | 16 | 1.8829 |
| `shuffle_late_N4` | 10,800 | 17 | 1.8824 |

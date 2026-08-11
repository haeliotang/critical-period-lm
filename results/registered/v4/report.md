# Study report

**Verdict:** `INCONCLUSIVE`

## Basis

- exponent delta +0.438 and two-sided p 0.0079 settle neither an onset effect nor its absence against a margin of 0.501
- shuffle_early_N4 read LIKE_CONTROL: early damage is repaired at the same rate as the information-preserving control

## How fast is the damage repaired?

Gap to baseline, paired by seed, fitted as `gap(T) = c / T^alpha`. Each seed is
fitted separately and the interval is across seeds.

**Every reading is taken against the negative control, not against a theoretical
value.** `alpha` mixes the deficit's cost with the baseline curve's own shape, and
that shape is common to every condition at a rung, so it cancels in a comparison and
nowhere else. What this buys is a comparative answer; what it gives up is the
absolute one — whether damage is a lag or a scar is out of scope, see `CLAIMS.md`.

| Condition | 2,700 | 5,400 | 10,800 | alpha | 95% interval | vs control | p | reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fixed_early_N4` | +0.1045 | +0.0447 | +0.0196 | 1.227 | [1.020, 1.434] | anchor | — | ANCHOR (the reference every other condition is read against) |
| `shuffle_early_N4` | +0.1007 | +0.0459 | +0.0195 | 1.193 | [1.076, 1.310] | -0.034 | 0.7460 | LIKE_CONTROL (repairs at the control's rate) |
| `shuffle_late_N4` | +0.0633 | +0.0387 | +0.0222 | 0.756 | [0.744, 0.767] | -0.472 | 0.0079 | UNDETERMINED |

### Descriptive only: what a pure lag would have predicted

Reported so a reader can see the assumption fail rather than take it on trust.
Neither number gates anything.

- Baseline local log-slopes between rungs: 0.3675, 0.2645
- Naive pure-lag exponent, valid only if those slopes are equal: 1.000
- Corrected for how they actually move: 1.237

The correction rests on a handful of slope estimates from a handful of points. It is
enough to show that an anchor of 1 is wrong; it is not enough to be an anchor.

## Instrument

- Top budget: 10,800 steps
- Baseline seed SD at the top budget: 0.0029
- Level floor (is there damage to model): 0.0100 nats
- Exponent margin (from the control's own seed spread): 0.501

## Primary contrast: does onset change the decay rate?

A critical period predicts early damage is the harder to repair, so it should decay
*more slowly*: `alpha_early < alpha_late`. The one-sided test is that prediction.
The two-sided test exists so that an onset effect running the other way is reported
rather than absorbed into a null.

- alpha(early) − alpha(late): +0.438
- One-sided p, critical-period direction: 1.0000
- Two-sided p, onset matters either way: 0.0079

## Per-seed exponents

| Condition | seeds fitted | seeds dropped | per-seed alpha |
| --- | --- | --- | --- |
| `fixed_early_N4` | 5 | 0 | 1.075, 1.160, 1.149, 1.247, 1.505 |
| `shuffle_early_N4` | 5 | 0 | 1.081, 1.219, 1.108, 1.291, 1.266 |
| `shuffle_late_N4` | 5 | 0 | 0.754, 0.744, 0.758, 0.769, 0.754 |

## Runs dropped for want of a baseline partner

None. Every deficit run had a baseline partner at its budget and seed.

## Runs included

Every run record found was included. There is no exclusion rule.

| Condition | Budget | Seed | Final eval loss |
| --- | --- | --- | --- |
| `baseline` | 2,700 | 5 | 2.2906 |
| `baseline` | 2,700 | 6 | 2.3001 |
| `baseline` | 2,700 | 7 | 2.2955 |
| `baseline` | 2,700 | 8 | 2.2973 |
| `baseline` | 2,700 | 9 | 2.2994 |
| `baseline` | 5,400 | 5 | 2.0396 |
| `baseline` | 5,400 | 6 | 2.0448 |
| `baseline` | 5,400 | 7 | 2.0344 |
| `baseline` | 5,400 | 8 | 2.0472 |
| `baseline` | 5,400 | 9 | 2.0434 |
| `baseline` | 10,800 | 5 | 1.8540 |
| `baseline` | 10,800 | 6 | 1.8590 |
| `baseline` | 10,800 | 7 | 1.8582 |
| `baseline` | 10,800 | 8 | 1.8595 |
| `baseline` | 10,800 | 9 | 1.8620 |
| `fixed_early_N4` | 2,700 | 5 | 2.4133 |
| `fixed_early_N4` | 2,700 | 6 | 2.3920 |
| `fixed_early_N4` | 2,700 | 7 | 2.3985 |
| `fixed_early_N4` | 2,700 | 8 | 2.4025 |
| `fixed_early_N4` | 2,700 | 9 | 2.3993 |
| `fixed_early_N4` | 5,400 | 5 | 2.0830 |
| `fixed_early_N4` | 5,400 | 6 | 2.0935 |
| `fixed_early_N4` | 5,400 | 7 | 2.0863 |
| `fixed_early_N4` | 5,400 | 8 | 2.0859 |
| `fixed_early_N4` | 5,400 | 9 | 2.0843 |
| `fixed_early_N4` | 10,800 | 5 | 1.8816 |
| `fixed_early_N4` | 10,800 | 6 | 1.8774 |
| `fixed_early_N4` | 10,800 | 7 | 1.8791 |
| `fixed_early_N4` | 10,800 | 8 | 1.8782 |
| `fixed_early_N4` | 10,800 | 9 | 1.8744 |
| `shuffle_early_N4` | 2,700 | 5 | 2.3968 |
| `shuffle_early_N4` | 2,700 | 6 | 2.4065 |
| `shuffle_early_N4` | 2,700 | 7 | 2.3984 |
| `shuffle_early_N4` | 2,700 | 8 | 2.4007 |
| `shuffle_early_N4` | 2,700 | 9 | 2.3842 |
| `shuffle_early_N4` | 5,400 | 5 | 2.0885 |
| `shuffle_early_N4` | 5,400 | 6 | 2.0910 |
| `shuffle_early_N4` | 5,400 | 7 | 2.0841 |
| `shuffle_early_N4` | 5,400 | 8 | 2.0869 |
| `shuffle_early_N4` | 5,400 | 9 | 2.0885 |
| `shuffle_early_N4` | 10,800 | 5 | 1.8777 |
| `shuffle_early_N4` | 10,800 | 6 | 1.8786 |
| `shuffle_early_N4` | 10,800 | 7 | 1.8803 |
| `shuffle_early_N4` | 10,800 | 8 | 1.8768 |
| `shuffle_early_N4` | 10,800 | 9 | 1.8767 |
| `shuffle_late_N4` | 2,700 | 5 | 2.3543 |
| `shuffle_late_N4` | 2,700 | 6 | 2.3642 |
| `shuffle_late_N4` | 2,700 | 7 | 2.3565 |
| `shuffle_late_N4` | 2,700 | 8 | 2.3610 |
| `shuffle_late_N4` | 2,700 | 9 | 2.3633 |
| `shuffle_late_N4` | 5,400 | 5 | 2.0788 |
| `shuffle_late_N4` | 5,400 | 6 | 2.0825 |
| `shuffle_late_N4` | 5,400 | 7 | 2.0732 |
| `shuffle_late_N4` | 5,400 | 8 | 2.0873 |
| `shuffle_late_N4` | 5,400 | 9 | 2.0809 |
| `shuffle_late_N4` | 10,800 | 5 | 1.8764 |
| `shuffle_late_N4` | 10,800 | 6 | 1.8819 |
| `shuffle_late_N4` | 10,800 | 7 | 1.8795 |
| `shuffle_late_N4` | 10,800 | 8 | 1.8815 |
| `shuffle_late_N4` | 10,800 | 9 | 1.8845 |

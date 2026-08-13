# Could the late arm's smaller recovery allowance explain the exponent difference?

**POST-HOC DESCRIPTIVE CHECK. NOT A REGISTERED ANALYSIS.** It answers the question a reviewer asks first and changes no verdict.

## The handicap is real, and it is the same at every rung

The deficit is a fixed fraction of each rung's own budget, so every ratio that
defines the treatment is scale-invariant. Measured rather than assumed:

| Budget | Deficit | Share of run | Early recovery | Late recovery | Step ratio | LR-area ratio |
| --- | --- | --- | --- | --- | --- | --- |
| 1,350 | 100 | 7.4% | 1,250 | 938 | 0.7504 | 0.5136 |
| 2,700 | 200 | 7.4% | 2,500 | 1,875 | 0.7500 | 0.5128 |
| 5,400 | 400 | 7.4% | 5,000 | 3,750 | 0.7500 | 0.5128 |
| 10,800 | 800 | 7.4% | 10,000 | 7,500 | 0.7500 | 0.5127 |

Step ratio varies by 0.0004 across the ladder and the learning-rate-area
ratio by 0.0009. The residual comes from rounding the onset to whole steps
at the smallest rung, not from the design.

## A constant handicap moves the amplitude and not the exponent

The early arm's own gaps, scaled by a constant and refitted:

| Multiplier | Shift in exponent |
| --- | --- |
| ×0.5 | 0.00e+00 |
| ×0.75 | 0.00e+00 |
| ×1.5 | 0.00e+00 |
| ×2.0 | 0.00e+00 |
| ×10.0 | 0.00e+00 |

Exactly zero, at every multiplier. This is what a power law is, not an approximation
that happens to hold here.

## What a handicap would have to look like instead

- Observed exponent difference: **0.387** — fitted here on rung-mean gaps,
  where the registered contrast averages per-seed exponents. The two differ in the
  third decimal and the argument does not turn on which is used.
- Budget span: 1,350 to 10,800, 3 doublings
- A handicap could produce it only by growing as `T^0.387` — becoming
  **2.24× more severe** in relative terms at the top rung than the bottom
- Measured growth in the handicap across that span: 0.0009 on a ratio of 0.514, i.e. **0.18%**

The shape the explanation needs is not available in this design.

## Where the handicap did leave a trace

| Condition | Exponent | Amplitude |
| --- | --- | --- |
| `fixed_early_N4` | 1.151 | 871.0 |
| `shuffle_early_N4` | 1.150 | 871.0 |
| `shuffle_late_N4` | 0.763 | 26.8 |

The control and the early arm are the same power law in **both** parameters. The late
arm differs in both. A constant handicap can only move the second column, so it cannot
be what separates the third row from the first two.

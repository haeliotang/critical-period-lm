# Design v5 draft: fixing the margin, without pretending the fix is innocent

**Status: DRAFT. Not active, not frozen.** The design of record is `preregistration.md` at
`v4`, frozen at tag `cplm-design-v4-frozen`, and the registered result under it is
`INCONCLUSIVE`. **That result stands and is never superseded by anything here.**

---

## 1. The defect, stated so that it does not depend on the outcome

The registered exponent margin is `3 × SD` of the control's five per-seed exponents. Two
things are wrong with that, and both would have been wrong whichever way the effect went.

**A scale estimated from five numbers is itself very noisy.** For normal data the sample
standard deviation at `n = 5` scatters by ±34% of the truth. The margin can therefore be
half or double its correct value from luck alone. Observed: 0.298 on seeds 0–4 and 0.501 on
seeds 5–9, from data whose effect estimate barely moved.

| Seeds per arm | Relative error of the sample SD |
| --- | --- |
| 5 | ±34% |
| 8 | ±26% |
| 10 | ±23% |
| 15 | ±19% |

**The bar for a contrast is imported from a condition that is not in it.** The primary
contrast is early against late. In the registered run their per-seed exponents scattered by
0.094 and 0.009 — both well determined. The control's scattered by 0.167, and it alone set
the bar at 0.501. A third condition's bad luck decided whether a difference between two
well-measured ones counted.

## 2. The thing that must be said out loud

**Every correct fix to this defect makes the observed effect clear the bar.** That is not a
coincidence and it is not evidence for the fix — it is what "the defect is what produced
`INCONCLUSIVE`" means. Diagnostics from the registered run, **for design only, never to be
applied to those records**:

| Scale source | Implied margin | Observed Δ = 0.438 |
| --- | --- | --- |
| Control alone (registered, `n = 5`) | 0.501 | does not clear |
| Pooled across all three conditions | 0.332 | clears |
| Pooled across the two contrasted arms | 0.201 | clears |

A reader is entitled to see that pattern and to discount accordingly. The mitigations are
the only answer available: the fix is declared before new data, it is justified by a fact
about estimators rather than by this result, it is tested on **new seeds**, and the v4
inconclusive result is reported in full alongside whatever v5 produces.

## 3. Two paths, and they differ in what a sceptic has to take on trust

### Path 1 — change nothing in the rules; make the instrument good enough for them

Keep `margin = 3 × SD(control)` exactly as frozen. Reduce the control's actual scatter and
estimate it from more seeds, so the rule stops being hostage to luck.

Nothing about the decision procedure moves, so there is no goalpost to accuse anyone of
moving. It costs compute instead of credibility.

### Path 2 — change where the scale comes from

Replace the control-only scale with a pooled within-condition scale across all conditions:
`sqrt(mean of the per-condition variances)`, `df = 12` instead of 4 at five seeds.

The **criterion** is unchanged — three times the exponent noise. Only the **estimator** of
that noise changes, and it changes for a reason that is true of estimators generally. But it
alters the number in the helpful direction on data already seen, and Section 2 is the honest
disclosure of that.

## 4. Instrument changes, common to both paths

**Add a rung below, not above.** The ladder currently runs 2,700 / 5,400 / 10,800. At the
top rung the gap is about 0.020 against a baseline seed SD of 0.0029, so one unlucky baseline
run compresses that seed's gap and levers the log fit — which is exactly how the control's
1.505 outlier arose. **Extending the ladder upward makes this worse**, because the gap keeps
shrinking toward the noise floor. A rung at **1,350** has a gap near 0.20, is the most
precisely measured point available, anchors the fit, and costs 1.9 hours.

Registered risk: at 1,350 steps the model is early enough that the power law may not hold
there. The fit must be reported both with and without the low rung, and a disagreement
between them is a finding about the model, not a nuisance to be smoothed over.

**More seeds.** The margin's stability is a degrees-of-freedom problem and seeds are the only
thing that buys degrees of freedom under Path 1.

**Not worth doing:** more evaluation batches. Gaps are paired against the same fixed
evaluation set, so evaluation sampling noise largely cancels in the difference. The residual
scatter is genuine model-to-model variation, and only seeds average that down.

## 5. Cost

Four conditions, at the measured 3.97 steps/s.

| Plan | Rungs | Seeds | Steps | Wall clock |
| --- | --- | --- | --- | --- |
| Repeat v4 unchanged | 3 | 5 | 378,000 | 26.4 h |
| Path 2 + low rung | 4 | 5 | 405,000 | 28.3 h |
| Path 1, lean | 4 | 8 | 648,000 | 45.3 h |
| Path 1, full | 4 | 10 | 810,000 | 56.7 h |

Seeds **10 onward**, never reused. Under Path 1 at eight seeds the two-sided permutation
floor is 2/12870, and the margin's relative error falls from ±34% to ±26%.

## 6. What v5 does not change

The endpoint, the deficits, the control's identity, the geometry, the schedule, the pairing,
the freeze mechanics, the claim register's scope limits, and the exclusion of the absolute
lag-versus-scar question. Only the scale that sets the bar, and the precision behind it.

## 7. Reporting obligation

Whatever v5 returns, the write-up carries both: the v4 registered result of `INCONCLUSIVE`
with its diagnosed cause, and the v5 result with the ordering in Section 2 stated plainly.
An improved instrument that gets a cleaner answer is a normal scientific outcome. An improved
instrument presented without the first answer is not.

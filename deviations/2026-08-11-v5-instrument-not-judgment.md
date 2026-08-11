# Design v5: a better instrument, with the judgment code left untouched

**Date:** 2026-08-11
**Design version:** v4 to v5
**Decided:** after reading the v4 registered result, and because of it
**Supersedes nothing.** The v4 registered result of `INCONCLUSIVE` stands on its own records
at `runs/v4/` and `results/registered/v4/`, and is reported alongside whatever v5 returns.

## The defect, stated so it does not depend on the outcome

The exponent margin is `3 × SD` of the control's per-seed exponents. Two things are wrong
with that, and both would have been wrong whichever way the effect went.

**A scale estimated from five numbers is itself very noisy.** For normal data the sample
standard deviation at `n = 5` scatters by ±34% of the truth, so the margin can be half or
double its correct value from luck alone. Observed: 0.298 on seeds 0–4 and 0.501 on seeds
5–9, from data whose effect estimate moved from +0.392 to +0.438.

**The scatter itself was avoidable.** At the top rung the gap is about 0.020 against a
baseline seed SD of 0.0029. One unlucky baseline run compresses that seed's gap and levers
the log fit at its endpoint. In the v4 run this produced a control exponent of 1.505 against
1.075–1.247 for the other four seeds, and that one seed roughly doubled the margin.

## What was NOT changed, and why that matters

**`decision_rules.py` is byte-identical between v4 and v5.**

    v4  0dd42ed5566b838e61999851a6cec8d2dadcde6d370165739370f79f7eabc048
    v5  0dd42ed5566b838e61999851a6cec8d2dadcde6d370165739370f79f7eabc048

Both hashes are in the respective `freeze-manifest.json`, so this is checkable rather than
asserted. The margin formula, the readings, the tests, the verdicts and the primary contrast
are exactly what they were before the v4 result was seen.

This was a deliberate choice between two paths. Changing where the scale comes from — pooling
across conditions, say — would have been cheaper and is defensible on its own statistical
merits, but it alters a decision rule after seeing the result it disfavoured. On the v4 data
a pooled scale gives a margin of 0.332 and a scale from the two contrasted arms gives 0.201,
against an observed difference of 0.438. **Every correct fix to this defect makes the
observed effect clear the bar**, which is what "the defect is what produced `INCONCLUSIVE`"
means — and precisely why the cheaper path would have been impossible to distinguish from
moving the goalposts. v5 spends compute instead of credibility.

## What changed

**A fourth rung, below the others.** 1,350 / 2,700 / 5,400 / 10,800. Extending upward would
make things worse: the gap keeps shrinking toward the noise floor. At 1,350 the gap is near
0.20 — the most precisely measured point available — and it anchors the fit from the other
end. Cost, 1.9 hours.

Registered risk: the power law may not hold that early. The exponent is reported **both with
and without the low rung**, the four-rung fit is the registered one, and a disagreement
between them is a finding rather than a nuisance.

**Eight seeds instead of five.** Seeds are the only thing that buys degrees of freedom under
an unchanged rule. The sample SD's relative error falls from ±34% to ±26% and the two-sided
permutation floor from 0.008 to 0.00016.

**Seed indices 10–17.** Calibration used 0–4, the v4 ladder used 5–9. No seed is reused: a
registered run on seeds already seen is a recomputation, not a replication.

**Records are scoped by design version.** `runs/v5/` and `results/registered/v5/`, so v4's
evidence stays intact and the two ladders can never be analysed together. This is a trainer
and driver change; neither is in the freeze corpus.

## Cost

32 condition-seed combinations over four rungs: 648,000 steps, about 45.3 hours.

## Reporting obligation

The write-up carries both results. An improved instrument that returns a cleaner answer is a
normal scientific outcome; an improved instrument presented without the first answer is not.

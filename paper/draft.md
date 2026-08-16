# No critical period in language-model pretraining, and an onset effect running the other way

*Preregistered ladder experiments in small language models.*

**Draft.** Target venue: BabyLM workshop. Every number below is traceable to
`results/registered/`, and every claim is bounded by `CLAIMS.md`.

---

## Abstract

Vision networks have critical periods: a stimulus deficit applied during an early window of
training permanently reduces final accuracy, however long the network is afterwards trained
on clean data. We test the analogous claim in autoregressive language-model pretraining, and
find no critical period — but an onset effect running the other way.

Because a loss difference at a single training budget cannot distinguish permanent damage
from recovery that has not finished, we measure the **rate** at which damage is repaired: the
same conditions are trained at a ladder of budgets and the gap to a seed-matched clean
baseline is fitted as `gap(T) = c/T^α`. The exponent is read against a negative control
measured in the same experiment, never against a theoretical value.

At 7.34M parameters on TinyStories, across four budget rungs and eight seeds, a
window-shuffle deficit applied at the very start of training is repaired at the same rate as
an information-preserving control of identical size and onset (Δα = −0.003, p = 0.95). The
same deficit applied at mid-training is not (Δα = −0.395, p = 0.0002). The two arms differ by
α = 0.392 (two-sided exact permutation p = 0.0002). Early damage starts nearly twice as large
as late damage and ends smaller; the curves cross.

We report two registered results, not one. A first registered run measured the same effect
(+0.438, and like this one a p-value pinned at the floor of its own permutation test) and
returned `INCONCLUSIVE`, because its margin — three times the control's
own seed scatter — came out larger than the effect. It is reported here in full, with its
cause. Had that run reused the seeds used for calibration it would have returned a positive
verdict that a genuine out-of-sample replication does not support.

---

## 1. Introduction

Achille, Rovere and Soatto (ICLR 2019) showed that convolutional networks have critical
periods: blur the training images during an early window and final accuracy is permanently
reduced, no matter how long the network is subsequently trained on clean data, while a
deficit that leaves low-level image statistics intact — a vertical flip — leaves no permanent
trace. The effect depends on *when* the deficit occurred, not only on how much of it there
was. It has since been shown to arise in deep linear networks too, so it is not an accident
of one architecture.

Does anything like this happen in language-model pretraining?

The closest existing evidence points away from it. Constantinescu et al. (TACL 2025) varied
the age of exposure to a second language and found **no** critical period; they had to insert
a plasticity-decreasing regularizer to manufacture one. Their manipulation is delayed
exposure to new material rather than degraded input during a window followed by clean input,
so it does not answer the question directly, but it sets the prior.

We ran the deficit-window protocol itself, and hit a measurement problem that turns out to be
the substance of the paper.

### 1.1 A level at one budget cannot answer this question

The natural endpoint is the held-out loss gap at the end of training. It does not work, and
the reason is not subtle: a deficit condition that is merely *behind* — still closing the gap,
just slower — produces the same final gap as one that is permanently damaged. In our own
exploratory runs the gap fell 42% on a single budget doubling, so the endpoint was scoring
where the run happened to stop.

Worse, the obvious fix makes it invisible. Annealing the learning rate to zero at the end of
training makes every run converge, which is exactly what one wants for comparability — and
it also freezes in place any condition that had not finished recovering. Under that schedule
a single-budget endpoint will report "permanent" by construction.

So we measure the rate instead.

### 1.2 What we measure

Each condition is trained at four budgets, each double the last. The gap to a seed-matched
clean baseline is fitted per seed as

    gap(T) = c / T^α

and α — how fast the damage is repaired as the budget grows — is the registered quantity.

**α is read against the negative control, never against a theoretical value.** The tidy
derivation that a pure lag gives α = 1 assumes the baseline learning curve's log-slope is
constant. Ours falls about 30% per doubling, so that anchor is wrong, and the value corrected
for the measured slopes is too fragile to replace it. The slope factor is common to every
condition at a rung, so it cancels in a comparison and cancels nowhere else.

This buys a comparative answer and gives up an absolute one. **Whether the damage is
permanent or merely slow to repair is out of scope in this study**, and Section 4 says why.

---

## 2. Method

### 2.1 Model and corpus

A 7.34M-parameter decoder-only transformer (8 layers, d=256, 8 heads, context 256, RoPE,
tied embeddings) trained from scratch on a 629 MB prefix of TinyStories — 158M tokens under a
4096-entry byte-level BPE fit on the training text only. The held-out split is the dataset's
own validation file, never subjected to a deficit and never used for any selection decision.
Training runs under MLX on an M1 Pro at 32.5k tokens/s.

Learning rate: linear warmup over 2% of the run, then cosine decay to exactly zero. The
schedule is a registered constant and a named scope limit — Pawlak (2025) reports that
critical-period effects in vision can be removed by a cyclic schedule, so any result here is conditional
on this one.

### 2.2 The two deficits

Both are applied to the training stream only.

**Deficit S** — within each non-overlapping window of 16 tokens, permute the order, resampled
for every window of every batch. This destroys local sequential structure while leaving every
sequence a permutation of itself.

**Deficit F (negative control)** — the *same* operation with a single permutation drawn once
for the whole study and reused everywhere. The reordering is therefore deterministic and
invertible: nothing is destroyed, and a model can in principle learn to read the scrambled
order.

Same operation, same locus, same surface magnitude, differing in exactly one property. That
is what a negative control has to be, and it took two attempts to get there — an earlier
control that permuted the vocabulary was refuted by its own data, leaving twelve times the
damage of the deficit it was supposed to bound.

### 2.3 The ladder

| | |
| --- | --- |
| Rungs | 1,350 / 2,700 / 5,400 / 10,800 optimizer steps |
| Conditions | baseline, `fixed_early_N4` (control), `shuffle_early_N4`, `shuffle_late_N4` |
| Seeds | 8 per condition per rung, indices 10–17 |
| Deficit duration | 7.4% of each rung's own budget |
| Late onset | 23.1% of each rung's own budget |
| Total | 128 runs |

Every ratio defining the treatment is a fraction of the rung's own budget, so the geometry is
scale-invariant. Gaps are paired within budget and seed; a seed fixes both the initialization
and the data order.

### 2.4 Statistics

Seeds are the replication unit. Each seed yields one exponent from an OLS fit in log-log
space, and inference is across seeds.

- **Per-condition readings** compare a condition's exponents with the control's by exact
  two-sided permutation, against a margin of three times the control's own per-seed scatter,
  floored at 0.10.
- **The primary contrast** is `α(early) − α(late)`, one-sided in the critical-period direction
  (early repairs *more slowly*), with a secondary two-sided test.
- Interval estimates on α are t-intervals across seeds. This is a normality assumption at
  eight seeds and is the design's weakest inference; **the primary contrast does not rest on
  it**, being an exact permutation test.

At eight versus eight the two-sided permutation floor is 2/12870 ≈ 0.00016.

---

## 3. Results

### 3.1 The curves cross

Mean gap to baseline, in nats per token:

| Condition | 1,350 | 2,700 | 5,400 | 10,800 | shrinkage over 8× |
| --- | --- | --- | --- | --- | --- |
| `fixed_early_N4` (control) | +0.2106 | +0.1030 | +0.0434 | +0.0197 | 10.7× |
| `shuffle_early_N4` | +0.2091 | +0.1019 | +0.0467 | +0.0190 | **11.0×** |
| `shuffle_late_N4` | +0.1097 | +0.0643 | +0.0381 | +0.0224 | **4.9×** |

Read the first and last columns together. Early damage begins nearly twice as large as late
damage and ends smaller.

![Left: gap to a seed-matched baseline against training budget, both axes logarithmic, with
fitted power laws. The control and the early arm lie on the same line; the late arm is
shallower and crosses them near 8,000 steps. Right: the eight per-seed exponents behind each
fit, with the registered margin shown as a band around the control's
mean.](figures/decay-v5.png)

**Figure 1.** Both panels are produced by `analysis/figure.py` from the registered records;
no value is entered by hand. *(a)* On log axes a power law is a straight line and α is its
slope. The fitted early and late curves meet at T ≈ 7,987 — inside the ladder, between the
third and fourth rungs. **A level endpoint would have reported whichever side of that
crossing its single budget happened to fall on**, which is the argument of Section 1.1 in one
picture. *(b)* The late arm's eight seeds span 0.735–0.803, a band narrower than its distance
from the other sixteen, so the contrast is not one seed's doing. The control's own spread —
0.942–1.302, the widest of the three — is what the registered margin is three times of, and
is why the same effect could fail to clear it.

### 3.2 Early damage is indistinguishable from the control

| Condition | α | 95% interval | vs control | p | Reading |
| --- | --- | --- | --- | --- | --- |
| `fixed_early_N4` | 1.158 | [1.068, 1.248] | anchor | — | `ANCHOR` |
| `shuffle_early_N4` | 1.155 | [1.085, 1.225] | −0.003 | 0.9524 | `LIKE_CONTROL` |
| `shuffle_late_N4` | 0.763 | [0.744, 0.782] | −0.395 | 0.0002 | `SLOWER_THAN_CONTROL` |

Fitting amplitude as well as exponent sharpens this: the control and the early arm are the
same power law in **both** parameters (α 1.151 and 1.150, amplitude 871.0 and 871.0 on
rung-mean gaps). The late arm differs in both.

### 3.3 The primary contrast

`α(early) − α(late) = +0.392`, two-sided exact permutation p = 0.0002, against a registered
margin of 0.323. One-sided p in the critical-period direction: 1.0000.

**Registered verdict: `REVERSE_ONSET_EFFECT`.** Onset changes the repair rate, in the
direction opposite to every critical-period account.

### 3.4 The other registered result

An earlier registered run, under a design differing from this one only in its instrument,
returned `INCONCLUSIVE`:

| Run | Seeds | Rungs | Δα | Two-sided p | Permutation floor | Margin | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v4 | 5–9 | 3 | +0.438 | 0.0079 | 2/252 = 0.0079 | 0.501 | `INCONCLUSIVE` |
| v5 | 10–17 | 4 | +0.392 | 0.0002 | 2/12870 = 0.00016 | 0.323 | `REVERSE_ONSET_EFFECT` |

Both p-values sit exactly on the floor of their own test — the separation was as complete as
five and eight seeds respectively can register, and the two floors differ only because the
seed counts do. The effect estimate replicated; the margin did not hold. The margin is three times the
control's own per-seed scatter, and in v4 one seed's exponent came out at 1.505 against
1.075–1.247 for the other four, because that seed's baseline at the top rung was the worst of
the five and compressed its gap. One seed roughly doubled the margin.

The defect is direction-neutral and would have been true whichever way the effect ran: a
scale estimated from five numbers scatters by ±34% of the truth, so the margin can halve or
double from luck alone. It did — 0.298 on one seed set, 0.501 on the next.

**v5 changed the instrument and not the judgment.** `decision_rules.py` hashes identically in
both freeze manifests. What changed was a fourth rung placed *below* the others — at the top
rung the gap is only about seven times the baseline seed SD, so extending upward would push
further into the noise — and eight seeds instead of five.

### 3.5 Robustness

**Specification multiverse.** 144 defensible specifications: four sources for the margin's
scale × three multiples × three floors × two exponent estimators × two rung sets, with the
verdict logic held fixed. v5's verdict holds in 138/144 (96%), dissenting only at the widest
margin taken from the noisiest scale source. v4's holds in 90/144 (62%) — **more than a third
of reasonable analysts would have called it positive.** Four specifications are excluded by
name with reasons rather than swept in, including anchoring on the refuted theoretical value.

**The recovery-asymmetry objection.** The late arm's deficit ends later, so it has less
training left: 75% of the early arm's post-deficit steps and 51% of its learning-rate area.
Under a level endpoint this was a genuine confound. Under an exponent endpoint it cannot be
one, because a handicap that is the same multiple at every rung moves the amplitude and
leaves the exponent exactly unchanged — we verify this numerically at multipliers from 0.5 to
10, shift 0.00e+00 throughout.

The handicap is constant: the step ratio varies by 0.0004 across the ladder and the
learning-rate-area ratio by 0.0009, residuals from rounding the onset to whole steps.
Producing the observed exponent difference would require the handicap to grow as `T^0.387` —
**2.24× more severe** at the top rung than the bottom. Measured growth: **0.18%**.

---

## 4. What this does not show

**Whether the damage is permanent.** Answering that requires the deficit's cost in effective
training steps held constant across rungs — a pure lag is exactly that quantity being
constant — which means inverting the baseline curve. Four rungs cannot pin it down; our
exploratory attempt returned 1370, 693, 882 effective steps for the control, a
non-monotonicity that is an artefact of interpolating between too few points. The question is
**dropped, not answered**, and no exponent reported here may be pressed into service for it.

**A mechanism.** None is identified and none is claimed. The one representational measure the
design registered — layerwise CKA — was never produced: no checkpoints were saved, so it is
not computable from the records, and re-running with checkpointing would be a new study. This
is recorded in `deviations/`; we state it rather than let the registered list imply a measure
was taken.

**Anything about scale, schedule, or other deficits.** 7.34M parameters, one corpus, one
learning-rate schedule, one deficit pair, one late onset chosen by fiat at half the clean
budget.

**Anything about development or cognition.** The study was motivated by a question about
whether a model with frozen weights can be said to have grown up. That framing may motivate;
it licenses nothing, and the claim register has forbidden any developmental reading since
before data existed.

---

## 5. Related work

**Vision.** Achille et al. (ICLR 2019) established the phenomenon and the protocol, including
the requirement for a control that leaves low-level statistics intact. Kleinman et al. (ICLR 2024)
show it in deep linear networks.

**Language models.** Constantinescu et al. (TACL 2025) found no critical period for delayed
second-language exposure and had to add a plasticity-decreasing regularizer to produce one.
Our result is a second negative on the critical-period question in a different paradigm —
degraded input during a window rather than delayed exposure to new material — and adds a
positive finding in the opposite direction that their design could not have seen.

**Moderators.** Pawlak (2025), replicating Achille et al. in vision, reports that
critical-period damage and warm-starting damage alike can be averted by a cyclic
learning-rate schedule: restarting the rate after the deficit nearly closes the gap to a
model trained from scratch. If that holds, a critical period is a property of a training
configuration rather than of learning as such, and every result here is conditional on the
schedule we registered.

That conditioning cuts in a specific direction worth stating. Our schedule warms up once and
then decays monotonically to zero; it never restarts. On Pawlak's account this is the regime
in which critical-period damage should be *most* visible, not least — and the early arm still
tracks the control to three decimals. The null we report is therefore not obviously an
artefact of a forgiving schedule. It could still be an artefact of a different one, and we
did not vary it.

**Corpus.** Eldan and Li's TinyStories provides a corpus at which models of this size produce
readable, measurable language behaviour.

---

## 6. Discussion

The finding we did not expect is not the absence of a critical period — the prior for that
was already unfavourable — but the presence of an onset effect running the other way, and the
precision with which early damage matches the control. To three decimal places in the
exponent and four significant figures in the amplitude, a deficit that destroys word order at
the very start of training is repaired exactly as fast as one that merely hides it behind a
fixed code.

One reading suggests itself. Rather than leave it as a gloss that no result could contradict,
we state what would refute it. Suppose that at the very start there is little structure to
disrupt, so the corruption is paid for in training time and nothing else. Then the early arm
should be equivalent to a clean run given a shorter budget — its damage describable as a
*constant* debt in effective training steps, the same debt at every rung. The late arm should
not be: disrupting structure that already exists should cost something that a fixed number of
steps does not buy back.

That is a prediction about exactly the quantity Section 4 puts out of scope, and it is out of
scope for the same reason it is the right test. Recovering an effective-step debt means
inverting the baseline learning curve, and four rungs cannot do it — our exploratory attempt
returned 1370, 693, 882 steps for the control, which is interpolation noise, not a trend. On a
denser ladder, **the early arm's debt should be flat across budgets and the late arm's should
grow.** If both are flat, or both grow, this reading is wrong and the exponent difference has
another source.

**We have no evidence for it now.** No representational measure was taken — the one the design
registered was never produced — and nothing in the exponents reported here discriminates
between this account and any other account predicting the same two slopes.

The methodological story may be the more transferable one. Three endpoints were tried and
discarded before this one, and each failed the same way: it smuggled a parameter in from
outside the experiment. A level at one budget smuggled in where the run stopped. A categorical
ladder verdict smuggled in an arbitrary 0.01-nat floor. An exponent read against α = 1
smuggled in a constant learning-curve slope that the same data showed falling. A
control-anchored comparison smuggles in nothing: every quantity it uses is measured in the
same runs.

And one procedural rule earned its place outright. **The registered run may not reuse any seed
the calibration used.** Calibration used seeds 0–4, the first registered run 5–9, the second
10–17. Had the first reused the calibration seeds it would have returned
`REVERSE_ONSET_EFFECT` and the freeze would have certified a result that a genuine
out-of-sample replication does not support. That interception is the single most valuable
thing the preregistration produced.

---

## Limitations

- The t-interval on α is a normality assumption at eight seeds. The primary contrast is an
  exact permutation test and does not depend on it.
- The power law is fitted over an 8× budget range and is an extrapolation outside it.
- The late onset is fixed at half the clean budget by fiat.
- Top-rung precision limits everything: the gap there is about seven times the baseline seed
  SD, and log-space fitting turns top-rung noise into exponent noise. This is what produced
  the v4 outlier and, through the margin, the v4 verdict.
- Three pilots failed before the first valid ladder, for reasons — a wrong denominator, a
  refuted control, a warmup that did not scale — that no amount of simulation would have
  found. They are recorded in `deviations/`.

## Registration and provenance

The design was frozen before each registered run and carried by an annotated git tag; six
files are hashed into a manifest that `make freeze-check` verifies, and the judgment code is
byte-identical between the two registered designs. Before the decision code was allowed to see
a real run it had to return each of its five verdicts correctly against fabricated ladders
with planted decay exponents.

**One disclosure the result must travel with.** The `REVERSE_ONSET_EFFECT` verdict category
was added to the claim register *after* exploratory data pointed at the pattern. The
exploratory data motivated giving it a name; it supplied no evidence for it, and the
registered runs are what do. Without a name for it the design would have absorbed the most
interesting thing in its own data into a null — but the ordering is recorded so a reader can
discount it as they see fit.

Every departure from the registered design, including one attempt to annotate the frozen text
that the freeze check rejected, is in `deviations/` with its date, its reason, and whether it
was decided before or after the affected result was visible.

---

## References

Achille, A., Rovere, M., & Soatto, S. (2019). Critical Learning Periods in Deep Networks.
*International Conference on Learning Representations*. arXiv:1711.08856.
*The arXiv record carries the title* Critical Learning Periods in Deep Neural Networks; *the
venue title is cited here.*

Constantinescu, I., Pimentel, T., Cotterell, R., & Warstadt, A. (2025). Investigating Critical
Period Effects in Language Acquisition through Neural Language Models. *Transactions of the
Association for Computational Linguistics*, 13, 96–120. arXiv:2407.19325.
*Circulated as a preprint in 2024 and presented at EMNLP 2024; the registered design cites the
preprint year.*

Eldan, R., & Li, Y. (2023). TinyStories: How Small Can Language Models Be and Still Speak
Coherent English? arXiv:2305.07759.

Kleinman, M., Achille, A., & Soatto, S. (2024). Critical Learning Periods Emerge Even in Deep
Linear Networks. *International Conference on Learning Representations*. arXiv:2308.12221
(2023).

Kornblith, S., Norouzi, M., Lee, H., & Hinton, G. (2019). Similarity of Neural Network
Representations Revisited. *International Conference on Machine Learning*. arXiv:1905.00414.
*Source of the CKA measure the design registered and never produced; see Section 4.*

Pawlak, S. (2025). On the Occurence of Critical Learning Periods in Neural Networks.
arXiv:2510.09687. *The misspelling is the published title's.* Experiments are on vision
networks, replicating and extending Achille et al.

**On these references.** Each was checked against its arXiv or ACL Anthology record while this
draft was written, and two attributions moved as a result: Kleinman et al. from 2023 to its
ICLR 2024 publication, and Constantinescu et al. from the 2024 preprint to the 2025 journal
volume. The frozen `preregistration.md` carries the earlier forms and is not edited to match —
a citation year is not part of the registered design, and the freeze is worth more than the
tidiness.

# Preregistration: Critical Learning Periods in Small Language Models

**Design version:** `v5`
**Status:** frozen. Calibration is complete; ladders 1 and 2 were exploratory and cannot
support any claim. The registered ladder runs under fresh seeds, for the reason in
Section 8.4.

---

## 1. Scope and decision boundary

This study asks one question: **how fast does the damage from a training-data deficit decay
as the training budget grows, and does that rate depend on when the deficit occurred?**

"Cannot be repaired by later training" is the claim a critical period makes, so the study
measures repair directly: the same conditions are run at a ladder of budgets, and the
registered quantity is the exponent of the decay — how quickly the gap to a clean baseline
falls as the budget grows, against the rate that lost training alone would explain.

The phenomenon is established in vision. Achille, Rovere and Soatto showed that a deficit
(image blur) applied during an early window of CNN training permanently reduces final
accuracy regardless of how long the network is subsequently trained on clean data, while a
deficit that does not disturb low-level image statistics (vertical flip) leaves no
permanent trace. The registered contribution here is the first systematic test of the same
protocol in autoregressive language modeling.

This is a claim about optimization dynamics and representation formation. It is **not** a
claim about development, childhood, learning in humans, consciousness, or model welfare.
Developmental language may appear in the motivation section of any write-up. It may not
appear in the results or conclusions. See `CLAIMS.md` for the binding claim register.

## 2. Fixed external reference

The design is a domain transfer of an existing protocol. It is not a new protocol.

- Achille, Rovere, Soatto. *Critical Learning Periods in Deep Networks*, ICLR 2019;
  circulated on arXiv as *Critical Learning Periods in Deep Neural Networks*
  (arXiv:1711.08856). Source of the deficit-window design, the recovery-budget logic, and
  the requirement for a statistics-preserving negative control. Note the title differs
  between the arXiv and ICLR records; cite the venue title.
- Kleinman, Achille, Soatto. *Critical Learning Periods Emerge Even in Deep Linear
  Networks* (arXiv:2308.12221, 2023). Evidence that the phenomenon is not an accident of a
  particular architecture.
- Eldan, Li. *TinyStories: How Small Can Language Models Be and Still Speak Coherent
  English?* (arXiv:2305.07759, 2023). Source of the corpus and the evidence that models at
  this parameter scale produce measurable, readable language behaviour.
- Kornblith, Norouzi, Lee, Hinton. *Similarity of Neural Network Representations
  Revisited* (arXiv:1905.00414, ICML 2019). Source of the CKA secondary measure.

### 2.1 Prior work that constrains the interpretation

Two results bear directly on what this study can conclude, and both were found after the
design was drafted. Neither makes the question redundant; both narrow the claim.

- Constantinescu, Pimentel, Cotterell, Warstadt. *Investigating Critical Period Effects in
  Language Acquisition through Neural Language Models*, TACL 2024 (arXiv:2407.19325).
  Language models show **no** critical period effect when exposure to a second language is
  delayed, and the authors had to insert a plasticity-decreasing regularizer to manufacture
  one. The manipulation is delayed exposure to new material, not degraded input during an
  early window followed by clean input, so it does not answer the question registered here
  — but it is the closest existing evidence and it points away from an effect. The
  registered direction in Section 3.2 is retained because it is the direction the vision
  result predicts, not because it is the more likely outcome.
- Pawlak. *On the Occurrence of Critical Learning Periods in Neural Networks*
  (arXiv:2510.09687, 2025). Reports that critical-period effects and warm-starting damage
  can be avoided by cyclic learning-rate schedules. If that holds, a critical period is a
  property of a training configuration rather than of learning as such, and any result here
  is conditional on the registered schedule. The schedule is therefore a registered
  constant and a named scope limit, not an implementation detail.

Exact bibliographic identifiers were checked against the arXiv and venue records on
2026-08-06. Any later correction is a deviation entry, not a silent edit.

## 3. Registered question and comparison

### 3.1 Registered question

**How fast does the damage from a training-data deficit decay as the training budget grows,
and does that rate depend on when the deficit occurred?**

Each condition is run at a ladder of budgets. The gap to a seed-matched clean baseline is
fitted as `gap(T) = c / T^alpha`, and `alpha` is the registered quantity.

### 3.2 The control is the anchor, and what that costs

`alpha` is read against the negative control's own exponent, measured in the same
experiment, and never against a theoretical value.

The reason is that `alpha` mixes two things. Under a learning curve `loss ≈ a − b·ln(t)`, a
deficit costing `Δ` effective steps leaves `gap = b(T)·Δ/T`. The `b(T)` factor belongs to
the baseline curve, not to the deficit. Ladder 2 measured it falling 30% per doubling, so
the tidy derivation `alpha = 1` — which silently assumes `b` constant — does not hold, and
the corrected value near 1.3 rests on two slope estimates from three points and is far too
fragile to put in its place. `b(T)` is common to every condition at a rung, so it cancels
in a comparison and cancels nowhere else.

### 3.2.1 What this design does not answer

**Whether the damage is a lag or a scar is out of scope.** That is an absolute question and
answering it requires `Δ_eff`, the cost in effective training steps, estimated across rungs:
a pure lag is exactly `Δ_eff` constant. Estimating it means inverting the baseline curve,
and three rungs cannot pin that down — ladder 2 returned 1370, 693, 882 effective steps for
the control, a non-monotonicity that is an artefact of interpolating between three points.

The question needs a denser ladder and is a larger study. It is **dropped, not answered**,
and no `alpha` reported here may be used to answer it.

### 3.2.2 What it does answer

Comparative questions, which need no anchor:

| Contrast | Meaning |
| --- | --- |
| `alpha(condition) − alpha(control)` | is this deficit repaired at the control's rate? |
| `alpha(early) − alpha(late)` | does onset change the repair rate? |

Both are differences of exponents, so both are free of `b(T)`. They are also immune to a
constant proportional handicap on either arm — the recovery asymmetry that troubled every
earlier endpoint moves the amplitude `c` and leaves `alpha` alone.

### 3.3 Directional registered comparison

A critical period says early damage is the harder to repair, so it should decay **more
slowly**: `alpha_early < alpha_late`. That is the primary, one-sided test.

A **secondary, two-sided** test asks whether onset mattered in either direction. It exists
because ladder 1 pointed at the opposite pattern — late damage decaying more slowly — and a
design with no vocabulary for that would have absorbed the most interesting thing in its own
data into a null. The reverse finding is reported as `REVERSE_ONSET_EFFECT` and is
explicitly not a critical period.

### 3.4 Why the endpoint is an estimate and not a verdict at one budget

Two earlier endpoints failed, and each failure is recorded in `deviations/`.

A **level at one budget** could not tell a scar from unfinished recovery: the gap fell 42%
on a single doubling, so it was scoring where the run happened to stop.

A **categorical ladder verdict** fixed that but made every outcome hinge on an arbitrary
0.01-nat floor, and it went blind exactly where the conditions converged in level. In ladder
1 the top-rung contrast was +0.0003 nats at p = 0.50 — nothing — while the decay exponents
differed by 0.276. The level had lost a difference the rate still held.

### 3.5 Why onset, not dose, is the primary contrast

A deficit applied to the first `N` steps also consumes `N` steps of budget. A design that
varies only `N` cannot separate "early damage is special" from "more corrupted data is
worse". The early-versus-late contrast holds deficit type, duration and total budget fixed
and varies only onset. The duration sweep is deferred.


## 4. Design

### 4.1 Model and corpus

A decoder-only transformer trained from random initialization on the TinyStories corpus,
using a byte-level BPE tokenizer fit on the training split only. Architecture constants
(depth, width, heads, context length, vocabulary size), optimizer, learning-rate schedule,
and batch size are fixed by the calibration gate in Section 8.1 and frozen. They are not
tuned per condition. Every condition in the grid shares one configuration; conditions
differ only in the deficit schedule and the seed.

Training and evaluation run locally under MLX on Apple silicon. The hardware and the
measured throughput are recorded in the freeze so that the budget is auditable.

**The learning-rate schedule is linear warmup followed by cosine decay to exactly zero at
`T_total`.** This is a registered design decision, not a tuning choice, and the reason is
Section 4.5. Decaying to a fraction of peak leaves the loss still falling at the end of
training, which means "the model has recovered" is a state no run ever reaches; annealing
to zero makes convergence a property of the schedule rather than of the absolute step
count.

**Warmup is 2% of `T_total`, not a fixed step count.** This matters more than it sounds.
Pilot 2 used a fixed 500-step warmup, which was 9.3% of a 5,400-step run but 1.2% of a
43,200-step one — so the entire early deficit fell inside warmup at pilot scale and only 16%
of it did at full scale. The early arm was a different treatment at the two budgets, and the
learning-rate-weighted disturbance during the deficit differed between arms by 2.28× at
pilot scale against 0.92× at full scale.

Together these two make a claim that was asserted prematurely in design version v1.2 true:
**a scaled-down run rehearses a full-budget study rather than truncating one.** Convergence
follows the schedule, and now so does every ratio that defines the treatment. The earlier
version of this paragraph claimed the same thing on the strength of convergence alone; that
was wrong, and pilot 2 is where it was caught.

### 4.2 Deficits

Both deficits are applied to the *training* stream only. Evaluation data is never
corrupted, in any condition, at any time.

**Deficit S — window shuffle (predicted to scar).** Within each non-overlapping window of
`W` consecutive tokens, apply a uniformly random permutation, resampled per window per
batch. This destroys local sequential structure — the low-level statistics an early layer
must acquire — while leaving the token-frequency distribution and the corpus vocabulary
untouched. It is the intended analogue of blur.

**Deficit F — fixed window permutation (negative control, predicted to recover).** Apply the
*same* operation as Deficit S — reorder tokens within each non-overlapping window of `W` —
but with a single permutation drawn once for the whole study and reused for every window of
every batch, instead of resampled. The reordering is therefore deterministic and
invertible: the sequence still contains everything the clean sequence contained, positionally
relabeled, and a model can in principle learn to read the scrambled order. Deficit S destroys
order information outright; Deficit F only hides it behind a fixed code.

Same operation, same locus, same surface magnitude, differing in exactly one property:
fixed versus resampled. That is what a negative control has to be.

**This replaces an earlier control that did not work.** Design versions up to v1.2 used a
vocabulary permutation, on the reasoning that a relabeled language is isomorphic to the
original and therefore harmless. Pilot 2 refuted it: at identical onset and duration the
vocabulary permutation left twelve times the damage of Deficit S (+0.0324 against +0.0027
nats), and the damage was permanent. With tied embeddings a vocabulary permutation
invalidates the whole input and output interface rather than perturbing the input — it is
not the analogue of a vertical flip, it is the analogue of replacing the eye. The reasoning
was wrong and the experiment said so; the deviation is recorded in `deviations/`.

Deficit F is load-bearing in two distinct ways, and both must be stated:

1. It is the **information-preserving control**. Without it, a scar under Deficit S is
   uninterpretable, because nothing rules out that any sufficiently disruptive early
   perturbation scars.
2. It is the **compute-matched control**. It consumes exactly the same `N` steps of
   budget on non-clean data, so it absorbs the "those steps were wasted" explanation.

If Deficit F scars, the design has failed and no critical-period claim may be made from
this study. See Section 7.3.

### 4.3 Registered ladder and seed plan

Base budget `B = 1,350` optimizer steps. Every condition is run at `B`, `2B`, `4B` and `8B`
— 1,350 / 2,700 / 5,400 / 10,800. The deficit geometry of Section 4.4 applies to each rung's
own budget.

| Condition | Deficit | Window | Seeds per rung |
| --- | --- | --- | --- |
| `baseline` | none | — | 8 |
| `shuffle_early_N4` | S | `[0, N4)` | 8 |
| `shuffle_late_N4` | S | `[0.5T, 0.5T + N4)` | 8 |
| `fixed_early_N4` | F | `[0, N4)` | 8 |

**The baseline must carry every seed index any deficit arm uses, at every rung.** Gaps are
paired by seed, so a deficit run whose seed has no baseline partner contributes nothing.

#### Why the fourth rung is below and not above

The design v4 ladder ran 2,700 / 5,400 / 10,800 and its registered result was
`INCONCLUSIVE` because the exponent margin — three times the control's own per-seed scatter
— came out at 0.501 against a difference of 0.438. The control's scatter was inflated by one
seed whose top-rung gap was 0.0124 against 0.0184–0.0276 for the others, because that seed's
baseline at the top rung was the worst of the five.

At the top rung the gap is about 0.020 against a baseline seed SD of 0.0029, so a single
unlucky baseline run compresses that seed's gap and levers the log fit at its endpoint.
**Extending the ladder upward makes this worse**, since the gap keeps shrinking toward the
noise floor. A rung at 1,350 has a gap near 0.20 — the most precisely measured point
available — and it anchors the fit from the other end.

**Registered risk.** At 1,350 steps the model is early enough that the power law may not
hold there. The exponent is therefore reported **both with and without the low rung**, and a
disagreement between the two is a finding about the model rather than a nuisance to be
smoothed away. Neither fit is preferred after the fact; the four-rung fit is the registered
one and the three-rung fit is reported beside it.

#### Why eight seeds

The margin is a scale estimated from the control's seeds, and a sample standard deviation is
itself noisy: at five seeds it scatters by ±34% of the truth, at eight by ±26%. Design v4's
margin came out 0.298 on one seed set and 0.501 on the next while the effect estimate barely
moved. Seeds are the only thing that buys degrees of freedom, and the exact permutation
floors improve alongside.

| Seeds per arm | One-sided floor | Two-sided floor | Relative error of the sample SD |
| --- | --- | --- | --- |
| 5 | 0.004 | 0.008 | ±34% |
| 8 | 0.00008 | 0.00016 | ±26% |

**Seed indices 10–17.** Calibration used 0–4 and the v4 registered ladder used 5–9. No seed
is ever reused: a registered run on seeds already seen is a recomputation, not a
replication.

The duration sweep (`N1` through `N3`) remains deferred. Out of scope without an amendment:
a late-onset arm for Deficit F, a finer onset sweep, deficits applied to evaluation data,
model-scale sweeps, architecture variation.

### 4.4 Recovery protocol

Every condition trains for the same total number of optimizer steps:
`T_total = N_max_registered + R · T`, with the recovery multiplier `R` frozen at `2.0`
before any run. Deficit conditions therefore receive strictly more clean steps after
deficit removal than the baseline receives in total.

`R` is registered in advance for one reason: "it did not recover" is otherwise always
answerable with "you did not train it long enough". A multiplier chosen after seeing the
curves is not evidence.

The baseline trains on clean data for the identical `T_total`, so no condition has a step
or token advantage over any other.

### 4.5 The recovery asymmetry, and why the schedule addresses it

The two arms are matched on total steps and on total clean steps — both see 40,000 clean
steps out of 43,200 at `T = 20,000`. They are **not** matched on training *after* the
deficit: the early arm has 40,000 steps left, the late arm 30,000. Post-deficit training is
what repairs damage, so this is not a cosmetic difference.

It matters exactly as much as the loss is still moving. Under the log-shaped tail measured
in calibration run 1, the difference between 40,000 and 30,000 remaining steps was worth
about 0.075 nats — seven times the margin floor, and comparable to the largest effect
observed anywhere in pilot 1. A design in which the arms differ by seven margins for
reasons having nothing to do with onset cannot test what it claims to test.

Annealing the learning rate to zero is the registered response. When both arms have
converged, remaining budget stops converting into loss, and the asymmetry stops being worth
anything. **The convergence check in Section 8.1 is therefore not a formality: it is the
condition under which the primary contrast is interpretable at all.** If the baseline does
not meet it, the study does not proceed.

The residual asymmetry runs against the registered direction — the early arm keeps whatever
advantage remains — so the primary test is conservative for the registered hypothesis. That
also means the reverse finding is uninterpretable rather than informative: a `late > early`
result is what the asymmetry predicts on its own and will be reported as such, never as
evidence against a critical period.

## 5. Outcomes

### 5.1 Measured quantity

Held-out cross-entropy in nats per token at the final step of each run, under the frozen
evaluation procedure.

From these the **gap**, paired within budget and seed:
`g(condition, budget, seed) = loss(condition) − loss(baseline)`. A seed fixes the
initialization and the data order, so pairing removes a variance component an unpaired
comparison would carry. **A deficit run with no baseline partner at the same budget and seed
contributes nothing and is reported as dropped** — see the seed-count requirement in
Section 4.3, which exists because ladder 1 wasted six runs on exactly this.

### 5.2 Budget ladder

Four rungs, each double the one below. Rungs and seed counts are frozen. Two rungs can show
that a gap changed; three are the minimum for fitting a rate; the fourth is what makes the
rate stable enough for the margin to mean something.

### 5.3 Fitting

For each condition and each seed independently, `alpha` is the slope of `−log(gap)` against
`log(budget)`. **Seeds are the replication unit**; the reported interval is a two-sided 95%
t-interval across per-seed estimates.

That is a normality assumption at five seeds, and it is this design's weakest link. It is
declared here rather than buried, and the primary contrast does not rely on it — the
contrast is an exact permutation test over per-seed exponents.

A seed whose gap is non-positive at any rung cannot be fitted in log space. It is dropped
and reported, never nudged by an epsilon: a gap at or below zero is noise around zero, not
decay, and forcing it into the logarithm would manufacture an exponent.

### 5.4 Margins

**Level floor** — `max(3·SD_baseline_top, 0.01)` nats. Used only to decide whether a
condition did any damage worth modelling. It no longer decides any verdict, which is the
point of moving to an estimate.

**Exponent margin** — `max(3·SD of the control's per-seed alphas, 0.10)`. Self-calibrating:
the control is the condition whose exponent the design predicts is exactly 1, so its own
seed spread is the natural scale for what counts as a real difference in exponent.

### 5.5 Per-condition readings

Every reading is a comparison with the control, by the frozen rules in `decision_rules.py`:

- **`ANCHOR`** — the control itself, the reference the others are read against.
- **`LIKE_CONTROL`** — difference from the control below the exponent margin and not
  rejected: repaired at the control's rate.
- **`SLOWER_THAN_CONTROL`** — rejected, and at least a margin below: repaired more slowly
  than an information-preserving deficit of the same size at the same onset.
- **`FASTER_THAN_CONTROL`** — rejected, and at least a margin above.
- **`NO_EFFECT`** — the top-rung gap is under the level floor; there was no damage to model.
- **`UNDETERMINED`** — the comparison settles nothing.

The naive anchor `alpha = 1` and the value corrected for the measured baseline slopes are
both **reported beside every exponent and gate nothing**. They are printed so a reader can
watch the assumption fail rather than take it on trust.

### 5.6 Primary contrast

`Δ = mean alpha_early − mean alpha_late`, over per-seed exponents.

- **Primary:** one-sided exact permutation test for `alpha_early < alpha_late`, `α = 0.05`.
- **Secondary:** two-sided exact permutation test, same statistic.

### 5.7 Study-level verdict

- `CRITICAL_PERIOD` — the one-sided test rejects and `−Δ ≥` exponent margin.
- `REVERSE_ONSET_EFFECT` — the two-sided test rejects with `Δ ≥` exponent margin: late
  damage outlasts early damage, which no critical-period account predicts.
- `NO_CRITICAL_PERIOD` — the two-sided test does not reject and `|Δ| <` exponent margin.
- `DESIGN_FAILURE` — no usable control. The control anchors every reading, so without a
  fitted control exponent nothing can be read. **A control far from `alpha = 1` is not a
  failure**; it is the anchor, and the v3 rule that failed the design for it was wrong.
- `INCONCLUSIVE` — otherwise.

### 5.8 Secondary measures

Descriptive only; none can promote, demote or qualify a primary verdict.

- The amplitude `c`, and `Δ_eff = c/b`: the wound's cost in effective training steps. Ladder
  1 put it at 700–1,000 steps and strongly sublinear in wound length — a sharper sentence
  than any scar/no-scar binary, and reportable in its own right.
- The budget at which each fitted law reaches the level floor, computed **from the power
  law**. The retired log-linear form predicted negative gaps one rung beyond the data and
  understated this quantity about twofold.
- Layerwise CKA, full loss curves, wall-clock and token counts.


## 6. Registered controls

**Negative control.** `fixed_early_N4` must return `TRANSIENT` or `NO_EFFECT` — its damage
must decay away as the budget grows. This is the design's own falsification test and it is
checked before any primary result is read. Under a ladder endpoint "the control recovers"
is finally a checkable statement rather than a hope: it means the gap goes to zero with
budget, which is exactly what the ladder measures.

**Null band.** The 5 baseline seeds supply the null distribution. Seed variance, not an
assumed noise model, defines what counts as a difference.

**Compute matching.** Within a rung, every condition trains for the same `T_total`, and the
gap is paired against the baseline at that same rung and seed. Across rungs, budget is the
treatment and is deliberately not matched.

**Evaluation integrity.** The validation split is never subjected to a deficit and is
never used for any selection decision. It is split off before any training begins and its
hash is recorded in the freeze.

## 7. Gates

### 7.1 Freeze gate

The freeze corpus is this document, `CLAIMS.md`, `src/critical_period_lm/decision_rules.py`,
`src/critical_period_lm/deficits.py`, and the two test files that hold those modules to
their registered behaviour. The deficits are bound because they define the manipulation;
the tests are bound because a rule whose rehearsal can be weakened later was not rehearsed.

The corpus is hashed into `freeze-manifest.json` and carried by an annotated git tag before
the first registered training run. Verification is `make freeze-check`, and `make
runs-check` refuses to pass if run artifacts exist while no freeze does.

### 7.2 Rehearsal gate

`decision_rules.py` must pass its synthetic rehearsal before it is frozen: on fabricated
run records it must return `CRITICAL_PERIOD` under a planted effect, `NO_CRITICAL_PERIOD`
under a planted null with adequate resolution, `INCONCLUSIVE` under a planted null with
inadequate resolution, and `DESIGN_FAILURE` when the negative control is planted to scar.
A judgment rule that has never been run against a known answer is not a registered rule.

### 7.3 Design-failure conditions

Each of these terminates the critical-period claim and is reported as a design failure,
not as a negative result:

- no usable `fixed_early` control: fewer than two of its seeds could be fitted, or its
  damage sits under the level floor. The control anchors every reading, so without a fitted
  control exponent nothing else can be read. **A control far from `alpha = 1` is not a
  failure** — it is the anchor, and the v3 rule that failed the design for it was wrong;
- the baseline does not carry every seed index used by a deficit arm at some rung;
- baseline seed variance at the top rung is large enough that the margin exceeds the change
  in baseline loss across the ladder, i.e. the instrument cannot resolve anything the extra
  budget did;
- any run diverges, produces non-finite loss, or terminates early, and the condition
  cannot be completed at the registered seed;
- fewer than two budget rungs completed, or fewer than two baseline seeds at the top rung;
- a deficit run has no baseline partner at its own budget and seed, so no gap exists for it.

Note that unequal `T_total` across runs is **not** a failure condition under this design.
Budget is the treatment variable of the ladder. Design versions up to v1.3 checked total
steps for equality across the grid, which under a ladder endpoint would fail every valid
study.

### 7.4 Budget gate

If the calibrated ladder exceeds the declared wall-clock ceiling, it is reduced before
freeze, in this fixed priority order: drop the top rung `4B` (leaving two rungs and a
weaker decay test), then reduce the primary arms from 4 seeds to 3. Never reduced: the
number of rungs below two, the baseline below 3 seeds per rung, the `fixed_early_N4`
condition, and the recovery multiplier `R`.

## 8. Calibration, before freeze

### 8.1 Calibration gate

The following are measured, not guessed, and are then frozen: throughput on the target
hardware, the clean budget `T`, the resulting `T_total`, the full grid wall-clock estimate,
and the architecture and optimizer constants.

**Convergence criterion.** `T` is admissible only if a clean baseline run at the resulting
`T_total` improves by **less than one registered margin over its final 10% of steps**.

The earlier wording — train until the loss "has visibly plateaued" — described a state that
does not exist. Under a log-shaped tail the improvement over the final fraction `f` is
`b·ln(1/(1−f))`, which is the same number at every budget: at the rate measured in
calibration run 1, the last 10% of training always bought 0.0275 nats whether the run was
20,000 steps or 200,000. No `T` satisfies a criterion of that form, which is why the
schedule now anneals to zero and why the criterion is stated against the margin.

The criterion is checked on the baseline only, before the grid runs, and it is a gate:
failing it means the design does not proceed at that `T`, not that the threshold moves.

Calibration runs are exploratory. They are labeled as such, they are excluded from every
analysis, and they are stored outside `runs/`. Nothing measured during calibration may be
used to choose the primary endpoint, the margin, the direction, or `R`.

### 8.2 The budget-doubling diagnostic has become the endpoint

This section previously registered a doubling diagnostic to be reported alongside a
single-budget verdict. Its first use showed that the diagnostic, not the verdict, was
carrying the information: the gap it was checking fell by 42% on one doubling, which meant
the single-budget endpoint had been scoring unfinished recovery as permanent damage.

The diagnostic is therefore no longer a side check. It is Section 5, and the ladder is the
design. What remains here is the calibration obligation it implies: the base budget `B` must
be chosen so that the top rung `4B` is reachable within the declared wall-clock ceiling,
because a ladder that cannot afford its top rung cannot answer the question.

### 8.3 The registered ladder uses fresh seeds

Calibration used seeds 0–4 and the v4 registered ladder used 5–9. **The v5 registered
ladder uses seeds 10–17.**

Reusing the calibration seeds would make the registered run a recomputation rather than a
replication: same configuration, same seeds, same numbers, and the freeze would be
ceremonial. The endpoint has been revised four times and every revision was informed by data
already seen; a genuine out-of-sample replication is the only thing that discharges that,
and it is what the freeze exists to buy.

### 8.4 What calibration may not touch

The deficit definitions, the condition grid shape, the primary contrast, the decision
rules, and the claim register. If calibration reveals that one of these is wrong, that is
a redesign and a new design version, not an adjustment.

## 9. Analysis and reporting rules

- `runs/` is append-only. Analysis code reads it and never writes to it.
- Every run emits an immutable record: config hash, seed, condition, deficit schedule,
  full loss curves, final metrics, environment, wall-clock.
- Verdicts are produced by frozen code, from the run records, in one pass.
- All completed runs enter the analysis. There is no exclusion rule other than the
  mechanical failure conditions in Section 7.3, and any exclusion is a deviation entry.
- Null and inconclusive results are reported with the same prominence as positive ones.
- Every departure from this document is appended to `deviations/`, with its date, its
  reason, and whether it preceded or followed sight of the affected result.

## 10. Amendments

Amendments before freeze edit this document and increment the design version. Amendments
after freeze are new files under `deviations/`; the frozen text is never edited. An
amendment that changes the primary endpoint, the direction, the margin, `R`, or the
decision rules invalidates the freeze and requires a new design version and a new tag.

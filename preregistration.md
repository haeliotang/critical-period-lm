# Preregistration: Critical Learning Periods in Small Language Models

**Design version:** `v2-draft` (not frozen)
**Status:** pre-calibration, pre-freeze. No training run may be registered against this
document until the calibration gate in Section 8.1 closes and the freeze tag exists.

---

## 1. Scope and decision boundary

This study asks one question: **does the damage from a training-data deficit go to zero as
the training budget grows, and does that depend on when the deficit occurred?**

"Cannot be repaired by later training" is the claim a critical period makes, so the study
measures repair directly: the same conditions are run at a ladder of budgets and the
registered quantity is whether the gap to a clean baseline shrinks as the budget grows.

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

**Does the damage from a training-data deficit go to zero as the training budget grows, and
does that depend on when the deficit occurred?**

Each condition is trained at a ladder of budgets. The quantity of interest is the gap to a
seed-matched clean baseline at each budget, and the registered question is about the shape
of that gap as a function of budget, not its value at any one budget.

### 3.2 Directional registered comparison

Registered direction: at the top rung of the ladder,
`gap(shuffle_early) > gap(shuffle_late)`, with the early arm's gap persisting rather than
decaying away.

The opposite result, or no difference, is a registered outcome and will be reported as
such. This design has no result that counts as a failed experiment; it has results that
count as a failed *design*, and those are enumerated in Section 7.3.

### 3.3 Why the endpoint is a decay and not a level

Design versions up to v1.3 scored damage as the loss difference at the end of a single
training budget. The Section 8.2 diagnostic showed that this cannot work here. At 5,400
steps the late-arm gap was 0.0370; at 10,800 it was 0.0213 — a fall of 42% on one doubling.

A difference that shrinks when you train longer is unrepaired damage, not permanent damage.
Worse, the fix that made runs converge — annealing the learning rate to zero — guarantees
that *every* condition stops moving at the end of its budget, including one that had not
finished recovering. Convergence under that schedule freezes the deficit in place rather
than resolving it, so a single-budget endpoint reports "permanent" for a state whose only
distinguishing feature is where the run happened to stop.

Three pilots at a single budget produced `DESIGN_FAILURE` each time, with every condition
including the negative control scoring as scarred. Under a decay endpoint that pattern has
an obvious reading: at those budgets nothing had finished recovering, so nothing could
recover. The endpoint was measuring the budget, not the deficit.

### 3.4 Why onset, not dose, is the primary contrast

A deficit applied to the first `N` steps also consumes `N` steps of budget. A design that
varies only `N` cannot separate "early damage is special" from "more corrupted data is
worse" or from "less effective training happened". The early-versus-late contrast holds
deficit type, duration, total steps and total tokens fixed and varies only onset. That is
the definition of a critical period, so it is the primary contrast. The duration sweep is
retained as a secondary, descriptive arm.


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

### 4.3 Registered ladder

Let `B` be the base budget in optimizer steps, fixed at calibration. Every condition is run
at `B`, `2B` and `4B`. Within each rung a run is `T_total` steps long and the deficit
geometry of Section 4.4 is applied to that rung's own budget, so a rung is a complete study
in miniature rather than a truncation of the rung above.

| Condition | Deficit | Window | Seeds per rung |
| --- | --- | --- | --- |
| `baseline` | none | — | 3 |
| `shuffle_early_N4` | S | `[0, N4)` | 4 |
| `shuffle_late_N4` | S | `[0.5T, 0.5T + N4)` | 4 |
| `fixed_early_N4` | F | `[0, N4)` | 3 |

The two `N4` arms carry four seeds because they form the primary contrast, where an exact
permutation test on 4 versus 4 reaches `p = 1/70 ≈ 0.014` while 3 versus 3 bottoms out at
0.05. The decay test does not need four: it permutes budget labels over all rungs at once,
so three rungs of three seeds already enumerate 1,680 assignments.

The duration sweep (`N1` through `N3`) is deferred. Under a ladder endpoint it multiplies
the run count by the number of rungs, and it is descriptive rather than load-bearing. Adding
it later requires an amendment, not a decision made while results are visible.

Out of scope and not to be added without an amendment: a late-onset arm for Deficit F, a
finer onset sweep, deficits applied to evaluation data, model-scale sweeps, and any
architecture variation.

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

Held-out cross-entropy in nats per token on the frozen validation split, at the final step
of each run, under the frozen evaluation procedure (fixed batch order, fixed context length,
no sampling).

From these, the **gap**: `g(condition, budget, seed) = loss(condition, budget, seed) −
loss(baseline, budget, seed)`, paired within budget and seed. A seed fixes both the
initialization and the data order, so pairing removes a variance component that an unpaired
comparison would carry. A deficit run with no baseline partner at the same budget and seed
contributes no gap and is reported as dropped.

### 5.2 Budget ladder

Every condition is run at each rung of a ladder of budgets in which each rung is double the
one below. The rungs and the seed counts are fixed at calibration and frozen. At least three
rungs are required: two can show that a gap changed, but not that it is decaying toward
something.

**Extension rule, registered in advance.** If the top rung leaves either `fixed_early_N4` or
`shuffle_early_N4` at `DECAYING_UNRESOLVED` — shrinking but not yet under the margin — one
further rung at `8B` is added, and the ladder is re-analysed with all four rungs.

Three properties make this a sequential rule rather than a licence to keep going until an
answer appears:

- it fires on `DECAYING_UNRESOLVED` alone, which is a statement about resolution, and is
  blind to the direction or size of every other result;
- at most one extension is permitted; a second `DECAYING_UNRESOLVED` is reported as the
  study's answer, with the crossing budget as an extrapolation;
- the trigger is evaluated by the frozen decision code, not by reading a plot.

Its purpose is to buy a decision point partway through, not to buy a better result. A ladder
that stops while its gaps are still visibly falling has measured a decay rate and not an
asymptote, and reporting that honestly is the alternative this rule is weighed against.

### 5.3 Margin

`margin = max(3 · SD_baseline, 0.01)` nats per token, where `SD_baseline` is the sample
standard deviation of baseline final loss **at the top rung**. Computed once, from baseline
seeds only, never pooled with deficit cells. The absolute floor exists because a
pathologically tight baseline would otherwise let a scientifically empty difference pass.

### 5.4 Decay test

For each condition, the registered statistic is the slope of its gap against `log2(budget)`,
across every seed and rung. The null is that budget is unrelated to gap, so **budget labels
are exchangeable over the observed gaps**, and the p-value is the exact proportion of label
assignments whose slope is at least as negative as the observed one. One-sided, `α = 0.05`.

A paired sign-flip test was considered and rejected: at three seeds it enumerates `2^3 = 8`
assignments, so its smallest attainable p-value is 0.125 and it could never reject. The
budget-label permutation over three rungs of three seeds enumerates `9!/(3!)^3 = 1680`
assignments and reaches `1/1680`.

### 5.5 Per-condition ladder verdicts

Assigned by the frozen rules in `src/critical_period_lm/decision_rules.py`. Prose may not
assign a verdict the frozen code did not return.

- **`TRANSIENT`** — the gap decays and is below the margin at the top rung. Later training
  repaired the damage.
- **`PERSISTENT`** — no detectable decay and the gap is above the margin at the top rung.
  The damage survived every budget increase this ladder applied.
- **`DECAYING_UNRESOLVED`** — decaying but still above the margin. Reported together with
  the budget at which the fitted line would cross the margin, explicitly labelled as an
  extrapolation.
- **`NO_EFFECT`** — below the margin throughout, with no detectable trend.

`PERSISTENT` means *survived this ladder*, never *permanent*. The strongest available
statement is bounded by the top rung, and the top rung is stated with the verdict.

### 5.6 Primary contrast

`Δ_primary = mean g(shuffle_early, top) − mean g(shuffle_late, top)`, tested by exact
one-sided permutation of condition labels at `α = 0.05`. One registered test; no correction
is applied to it and no other test may be substituted.

### 5.7 Study-level verdict

`CRITICAL_PERIOD` requires all of:

1. every `fixed_early` control returns `TRANSIENT` or `NO_EFFECT` (Section 7.3 otherwise);
2. `shuffle_early` returns `PERSISTENT` or `DECAYING_UNRESOLVED`;
3. the primary test rejects at `α = 0.05` in the registered direction;
4. `Δ_primary ≥ margin`.

`NO_CRITICAL_PERIOD` requires that the primary test does not reject and that its minimum
detectable effect is at or below the margin — that the study had the resolution to have seen
the effect. Where `shuffle_early` also returns `TRANSIENT` or `NO_EFFECT`, that is reported
alongside: early damage was repaired by later training rather than persisting.

Otherwise `INCONCLUSIVE`. If a control does not decay away: `DESIGN_FAILURE`.

### 5.8 Secondary measures

Descriptive only. No secondary measure can promote, demote or qualify a primary verdict.

- Gap and ladder verdict for every condition, including the duration sweep.
- Fitted decay slope and, where applicable, the extrapolated crossing budget.
- Layerwise CKA between each deficit run and its seed-matched baseline at the top rung.
- Full loss curves, wall-clock and token counts for every run.


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

- any `fixed_early` ladder returns `PERSISTENT` or `UNDETERMINED`, that is, its damage
  does not decay away;
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

### 8.3 What calibration may not touch

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

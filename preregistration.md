# Preregistration: Critical Learning Periods in Small Language Models

**Design version:** `v1.1-draft` (not frozen)
**Status:** pre-calibration, pre-freeze. No training run may be registered against this
document until the calibration gate in Section 8.1 closes and the freeze tag exists.

---

## 1. Scope and decision boundary

This study asks one question: **does a training-data deficit applied during an early
window of language-model pretraining cause damage that a large clean-training budget
cannot repair, and is that damage specific to *when* the deficit occurred rather than to
*how much* deficit there was?**

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

Under a fixed total training budget with a fixed clean-recovery allowance, does a
window-shuffle deficit applied to the **first** `N` steps of pretraining leave a larger
permanent penalty in held-out loss than the **same deficit, of the same duration, applied
to a later window**?

### 3.2 Directional registered comparison

Registered direction: `final_loss(shuffle_early) > final_loss(shuffle_late)`.

The opposite result, or no difference, is a registered outcome of this study and will be
reported as such. This design has no result that counts as a failed experiment; it has
results that count as a failed *design*, and those are enumerated in Section 7.3.

### 3.3 Why onset, not dose, is the primary contrast

A deficit applied to the first `N` steps also consumes `N` steps of training budget. A
design that varies only `N` — deficit from step 0, sweeping duration — cannot separate
"early damage is special" from "more corrupted data is worse" or from "less effective
training happened". The early-versus-late contrast holds deficit type, deficit duration,
total step count, and total token count fixed, and varies only the onset. That contrast is
the definition of a critical period, so it is the primary endpoint. The duration sweep is
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

### 4.2 Deficits

Both deficits are applied to the *training* stream only. Evaluation data is never
corrupted, in any condition, at any time.

**Deficit S — window shuffle (predicted to scar).** Within each non-overlapping window of
`W` consecutive tokens, apply a uniformly random permutation, resampled per window per
batch. This destroys local sequential structure — the low-level statistics an early layer
must acquire — while leaving the token-frequency distribution and the corpus vocabulary
untouched. It is the intended analogue of blur.

**Deficit P — vocabulary permutation (negative control, predicted to recover).** Apply a
single fixed bijection over token ids to inputs and targets alike, for the duration of the
deficit window, then remove it. The corrupted task is isomorphic to the clean task: every
statistical regularity survives, relabeled. A model trained under Deficit P learns a
perfectly good model of a relabeled language and must, on removal, remap its embedding and
output layers while its interior structure remains applicable. It is the intended analogue
of vertical flip.

Deficit P is load-bearing in two distinct ways, and both must be stated:

1. It is the **statistics-preserving control**. Without it, a scar under Deficit S is
   uninterpretable, because nothing rules out that any sufficiently disruptive early
   perturbation scars.
2. It is the **compute-matched control**. It consumes exactly the same `N` steps of
   budget on non-clean data, so it absorbs the "those steps were wasted" explanation.

If Deficit P scars, the design has failed and no critical-period claim may be made from
this study. See Section 7.3.

### 4.3 Registered condition grid

Let `T` be the frozen clean-training budget in optimizer steps, fixed at calibration.
Deficit durations are expressed as fractions of `T`: `N ∈ {0.02, 0.04, 0.08, 0.16} · T`,
denoted `N1 < N2 < N3 < N4`.

| Condition | Deficit | Window | Seeds |
| --- | --- | --- | --- |
| `baseline` | none | — | 5 |
| `shuffle_early_N4` | S | `[0, N4)` | 4 |
| `shuffle_late_N4` | S | `[0.5T, 0.5T + N4)` | 4 |
| `shuffle_early_{N1..N3}` | S | `[0, N)` | 3 each |
| `shuffle_late_{N1..N3}` | S | `[0.5T, 0.5T + N)` | 3 each |
| `permute_early_{N1..N4}` | P | `[0, N)` | 3 each |

The two `N4` cells carry four seeds because they form the primary contrast, and an exact
permutation test on 4 versus 4 can reach `p = 1/70 ≈ 0.014` while 3 versus 3 bottoms out
at `p = 0.05`. Seeds are drawn from a registered list, in order, never selected.

Out of scope for this study, and not to be added later without an amendment: a late-onset
arm for Deficit P, an onset sweep at finer resolution, deficits applied to evaluation
data, model-scale sweeps, and any architecture variation.

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

## 5. Outcomes

### 5.1 Primary endpoint

Mean held-out cross-entropy in nats per token on the frozen validation split, evaluated at
the final step `T_total`, under the frozen evaluation procedure (fixed batch order, fixed
context length, no sampling, no temperature).

Primary statistic: `Δ_primary = mean(shuffle_early_N4) − mean(shuffle_late_N4)`.

Primary test: exact one-sided permutation test over all 70 label assignments of the 8
runs, `α = 0.05`. This is a single registered test; no correction is applied to it and no
other test may be substituted for it.

### 5.2 Scar margin

A difference must clear both a statistical and a magnitude bar.

`margin = max(3 · SD_baseline, 0.01)` nats per token, where `SD_baseline` is the sample
standard deviation of final loss across the 5 baseline seeds. The absolute floor exists
because a pathologically small seed variance would otherwise let a scientifically empty
difference pass.

`SD_baseline` is computed from the baseline seeds only, and it is computed once. It is not
recomputed per cell and not pooled with deficit cells.

### 5.3 Per-cell verdicts

For each deficit cell, against the baseline: `SCAR`, `RECOVERED`, or `INCONCLUSIVE`,
assigned by the frozen rules in `src/critical_period_lm/decision_rules.py`. Prose in the
write-up may not assign a verdict that the frozen code did not return.

`RECOVERED` means *failure to detect a scar at this power*, not *proof of no scar*. Every
`RECOVERED` cell is reported together with its minimum detectable effect, and a cell whose
minimum detectable effect exceeds the margin is labeled **calibrated null (underpowered)**
rather than being reported as a clean negative.

### 5.4 Study-level verdict

`CRITICAL_PERIOD` requires all of:

1. every `permute_early` cell returns `RECOVERED` (Section 7.3 otherwise);
2. `shuffle_early_N4` returns `SCAR`;
3. the primary permutation test rejects at `α = 0.05` in the registered direction;
4. `Δ_primary ≥ margin`.

`NO_CRITICAL_PERIOD` requires that the primary test does not reject and that its minimum
detectable effect is at or below the margin — that is, that the study had the resolution to
have seen the effect.

Otherwise: `INCONCLUSIVE`. If the negative control fails: `DESIGN_FAILURE`.

### 5.5 Secondary measures

Descriptive only. No secondary measure can promote, demote, or qualify a primary verdict.

- Δ against baseline for every cell, with the duration trend across `N1..N4`.
- Layerwise CKA between each deficit run and a seed-matched baseline run at final step.
- Full training and validation loss curves, retained for every run.
- Wall-clock and token counts per run.

## 6. Registered controls

**Negative control.** `permute_early_{N1..N4}` must recover. This is the design's own
falsification test, and it is checked before any primary result is read.

**Null band.** The 5 baseline seeds supply the null distribution. Seed variance, not an
assumed noise model, defines what counts as a difference.

**Compute matching.** Enforced by construction: identical `T_total` for every run,
verified mechanically from the run records rather than asserted.

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

- any `permute_early` cell returns `SCAR`;
- baseline seed variance is large enough that `margin` exceeds the total baseline-to-random
  loss range by more than 10%, i.e. the instrument cannot resolve anything;
- any run diverges, produces non-finite loss, or terminates early, and the condition
  cannot be completed at the registered seed;
- recorded `T_total` is not identical across completed runs.

### 7.4 Budget gate

If the calibrated full grid exceeds the declared wall-clock ceiling, it is reduced before
freeze, in this fixed priority order: drop `N2`, then `N3`, then the `permute_early` cells
at `N1` and `N2`. Never reduced: the two `N4` primary cells below 4 seeds, the baseline
below 5 seeds, the `permute_early_N4` cell, and the recovery multiplier `R`.

## 8. Calibration, before freeze

### 8.1 Calibration gate

The following are measured, not guessed, and are then frozen: throughput on the target
hardware, the clean budget `T` at which baseline validation loss has visibly plateaued,
the resulting `T_total`, the full grid wall-clock estimate, and the architecture and
optimizer constants.

Calibration runs are exploratory. They are labeled as such, they are excluded from every
analysis, and they are stored outside `runs/`. Nothing measured during calibration may be
used to choose the primary endpoint, the margin, the direction, or `R`.

### 8.2 What calibration may not touch

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

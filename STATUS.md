# Study status

**Updated:** 2026-08-06
**Design version:** `v1.1-draft`
**Lifecycle state:** `DESIGN-DRAFT; PILOT-RUNNING; PRE-FREEZE`
**Authorized next action:** read out the running pilot, then settle the budget criterion,
`T`, and the Section 7.4 reduction. No registered training run is authorized.

The registered design, the claim register, the two deficits, the decision rules, the corpus
pipeline, the model, and the trainer all exist. `make check` passes: 68 tests, including the
Section 7.2 rehearsal gate, in which the frozen decision code returns each of its four
verdicts against a planted ground truth.

Nothing is frozen. `freeze-manifest.json` does not exist, so `make freeze-check` reports
"not frozen", the trainer refuses any non-calibration run, and `make runs-check` refuses to
pass if anything appears in `runs/`.

`runs/` is empty and `results/` is empty. Every number below came from an exploratory
calibration run under `calibration/`, which is excluded from every analysis.

## Corpus

Prepared from TinyStories: a 629 MB prefix of the training file, cut at a story boundary,
plus the dataset's own held-out validation file. Byte-level BPE, vocabulary 4096, fit on a
32 MB prefix of the training text only.

| | |
| --- | --- |
| Training tokens | 158,037,148 |
| Validation tokens | 4,861,596 |
| Compression | 4.0 bytes per token |
| Tokenizer sha256 | `31e918ff8888ba3b…` |

Digests for all three artifacts are in `data/manifest.json` and are folded into every run's
config hash, so a run record is bound to the corpus it was trained on.

## Calibration, run 1: throughput and trajectory

One baseline run, 10,000 steps, seed 0, on an M1 Pro with 16 GB.

| | |
| --- | --- |
| Model | 7.34M parameters, 6.30M non-embedding (8 layers, d=256, 8 heads, context 256) |
| Throughput | 32.5k tokens/s, 3.97 optimizer steps/s |
| Validation loss | 8.80 at step 0, 1.868 at step 10,000 |
| Still improving | 0.008–0.014 nats per 1,000 steps at the end |

**The model has not plateaued at 10,000 steps**, so `T` cannot be set there. The tail fits
`loss ≈ 4.25 − 0.261·ln(step)`, which is a power law rather than a plateau, so "visibly
plateaued" needs an operational threshold rather than an eyeball.

A useful coincidence for calibration: at 10,000 steps the model is improving at roughly
0.010 nats per 1,000 steps, which is exactly the registered margin floor. One margin floor
is worth about a thousand steps of training progress at that point in the curve.

## Budget, at 3.97 steps/s

Total steps per run are `T_total = N4 + R·T = 2.16·T` for every condition.

| `T` | `T_total` | Hours per run | Full grid, 43 runs | Reduced grid, 25 runs | Extrapolated final loss |
| --- | --- | --- | --- | --- | --- |
| 10,000 | 21,600 | 1.51 | 65 h (2.7 d) | 38 h (1.6 d) | 1.638 |
| 15,000 | 32,400 | 2.27 | 97 h (4.1 d) | 57 h (2.4 d) | 1.532 |
| 20,000 | 43,200 | 3.02 | 130 h (5.4 d) | 76 h (3.1 d) | 1.456 |

The reduced grid is the Section 7.4 priority order applied in full: drop `N2`, `N3`, and the
`permute_early` cells at `N1` and `N2`. These are continuous-load figures on a laptop and
make no allowance for thermal throttling or for the machine being used for anything else.

Disk is not a constraint: run records hold curves and metrics, no checkpoints. 25 GB free
after the corpus.

## What still has to happen before the freeze

1. **Pilot — running.** A scaled-down rehearsal of the primary contrast at 5,400 steps:
   5 baseline seeds plus 3 each of `shuffle_early_N4`, `shuffle_late_N4` and
   `permute_early_N4`, 14 runs, about 5.3 hours. It answers four things at once — baseline
   seed variance, whether Deficit S hurts, whether Deficit P recovers, and whether the
   analysis path works on real records instead of synthetic ones. `make pilot`.

   Seed variance is the number everything hangs on: `margin = max(3·SD_baseline, 0.01)`, so
   `SD_baseline` sets the magnitude bar, every per-cell verdict, and every minimum
   detectable effect. Measuring it at 5,400 steps is conservative — early-training variance
   is normally larger than late-training variance, so the resulting power estimate is a
   floor rather than a promise.
2. **Redefine the budget criterion.** "Plateaued" is unreachable under a log law; see the
   open question below. Whatever replaces it has to be written down before `T` is chosen,
   not after the pilot curves have been looked at.
3. **Apply the Section 7.4 budget gate** if the chosen grid exceeds the wall-clock ceiling,
   and declare the ceiling itself, which still does not exist.
4. ~~Verify the four bibliographic identifiers.~~ Done 2026-08-06, and it turned up two
   papers that were not in the draft; both are now in Section 2.1 and both narrow the
   claim. See the note below.

## Known open design questions

Recorded because they affect interpretation and are not yet settled. Settling them before
the freeze is an edit to the design; settling them after is an amendment.

- Deficit P may recover so quickly that it is a weak control. It rules out the compute-loss
  explanation regardless, but a near-instant recovery says less about the
  statistics-preserving comparison than a slower one would.
- The late-arm onset is fixed at `0.5T` by fiat, justified by symmetry and nothing else.
- Whether a window shuffle at the BPE-token level disturbs sub-word structure enough to be
  a lower-level deficit than intended.
- **There is no plateau to put `T` at, and this needs a decision before the freeze.** Under
  the fitted law `loss ≈ 4.25 − 0.261·ln(step)`, the improvement over the final fraction `f`
  of training is `0.261·ln(1/(1−f))` — which does not depend on `T_total` at all. The final
  10% of training buys 0.0275 nats whether the run is 20,000 steps or 200,000. So "train
  until the baseline has visibly plateaued" (Section 8.1) describes a state this curve never
  reaches, and no choice of `T` satisfies it.

  The consequence is sharper than a wording problem. "Permanent damage" was operationalised
  as a level difference that survives to the end of a generous recovery budget. If the
  baseline is still descending, a deficit condition that is merely *behind* — still closing
  the gap, just slower — produces the same final-level difference as one that is genuinely
  scarred. Level alone cannot separate a scar from a lag.

  The measurable version is the gap, not the level: a scar is permanent if the difference
  between the deficit condition and the baseline has stopped shrinking by the end of
  training. The run records already carry the eval curves needed to check this, so the pilot
  will show whether gap closure is a live problem or a theoretical one. **This is a change
  to the decision rules and has not been made.** It is recorded here as an open question
  rather than applied, because rewriting the judgment logic on the strength of an argument,
  before the data that would settle it exists, is the thing this repository is built to
  prevent.

This file is a mutable operational pointer and is not part of the freeze corpus.

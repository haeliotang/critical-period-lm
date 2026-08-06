# Study status

**Updated:** 2026-08-06
**Design version:** `v1.1-draft`
**Lifecycle state:** `DESIGN-DRAFT; PILOT-1-INVALID; PRE-FREEZE`
**Authorized next action:** settle the recovery-asymmetry question, then re-run the pilot at
the corrected geometry to find out whether the negative control recovers. No registered
training run is authorized, and no grid should run while the control is unproven.

The registered design, the claim register, the two deficits, the decision rules, the corpus
pipeline, the model, and the trainer all exist. `make check` passes: 73 tests, including the
Section 7.2 rehearsal gate, in which the frozen decision code returns each of its four
verdicts against a planted ground truth.

Nothing is frozen. `freeze-manifest.json` does not exist, so `make freeze-check` reports
"not frozen", the trainer refuses any non-calibration run, and `make runs-check` refuses to
pass if anything appears in `runs/`.

`runs/` is empty and `results/` is empty. Every number below came from exploratory runs
under `calibration/`, which are excluded from every registered analysis and cannot support
any claim in `CLAIMS.md`.

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

## Pilot 1: complete, invalid, informative

14 runs at 5,400 steps. Verdict `DESIGN_FAILURE` — the negative control scarred. Archived
under `calibration/archive/pilot1-wrong-geometry/`.

| Condition | n | Delta vs baseline | p | Verdict |
| --- | --- | --- | --- | --- |
| `permute_early_N4` | 3 | +0.0815 | 0.0179 | SCAR |
| `shuffle_late_N4` | 3 | +0.0564 | 0.0179 | SCAR |
| `shuffle_early_N4` | 3 | +0.0358 | 0.0179 | SCAR |

Baseline mean 2.0208, seed SD 0.0036, margin 0.0108. Primary contrast −0.0207 (p = 1.000):
the late arm was worse than the early arm, the opposite of the registered direction.

**The pilot was run at a geometry the design never specified, and that is an error on the
implementation side, not a finding.** `TrainConfig.schedule` resolved `onset_frac` and
`duration_frac` against the run length, while the design defines them as fractions of the
clean budget `T`, where `T_total = 2.16·T`. Consequences, all in the direction that would
manufacture this exact result:

| | Pilot 1 as run | Registered geometry |
| --- | --- | --- |
| Deficit length | 16.0% of the run | 7.4% of the run |
| Recovery-to-deficit ratio | 5.2 : 1 | 12.5 : 1 |
| Post-deficit steps, early arm | 4,536 | 40,000 |
| Post-deficit steps, late arm | 1,836 | 30,000 |
| Early : late recovery asymmetry | 2.47× | 1.33× |

`RECOVERY_MULTIPLIER = 2.0` was declared in `decision_rules.py` and referenced by no code at
all, so the registered budget arithmetic existed only in prose. It now lives in
`deficits.py` beside the code that applies it, with `steps_from_clean_budget` as the single
conversion point, and four tests in the freeze corpus pin the geometry.

### What pilot 1 does establish

- **The instrument is sharp.** Baseline seed SD is 0.0036 nats — a quarter of the margin
  floor. The margin therefore sits at 0.0108 and is set by the floor, not by noise. Seed
  variance is not going to be what limits this study.
- **Both deficits bite.** All three deficit cells separated from baseline at the smallest
  attainable p for 3 versus 5. The manipulations do something measurable.
- **The analysis path works on real records**, end to end, and returned `DESIGN_FAILURE`
  from the negative control before reading the primary contrast, which is the order the
  design specifies.

### What pilot 1 cannot establish, by construction

Whether Deficit P recovers **when it is given the recovery budget it was promised**. At
5,400 total steps there was effectively no recovery phase: the control spent 16% of the
entire run learning an embedding table that was then invalidated, and 4,536 steps later it
was still 0.08 nats behind. That is what a lag looks like, and it is indistinguishable here
from a scar — which is precisely the open question recorded below.

The reversed primary direction has the same status. The late arm had 2.5 times less
post-deficit training than the early arm in this geometry. "Late is worse" is what that
asymmetry predicts on its own, with no critical period involved.

### The asymmetry does not disappear at the correct geometry

Both arms get exactly 40,000 clean steps and 43,200 total steps, so they are matched on
compute. They are **not** matched on *post-deficit* training: 40,000 against 30,000, a
factor of 1.33. Recovery opportunity is what determines whether damage is repaired, so the
two arms are not interchangeable.

This runs against the registered direction, so the primary test is conservative: an
observed `early > late` would hold despite the handicap. But a null is correspondingly
weaker than it looks, and a `late > early` result is uninterpretable rather than
informative. The learning-rate schedule compounds it in the same direction — the late arm
sits and recovers at a lower point on the cosine decay. **This is a real design limitation
that nobody had noticed before the pilot, and it is not yet resolved.**

## What still has to happen before the freeze

1. **Decide what to do about the recovery asymmetry**, above. It is the one genuinely open
   design question; the others are arithmetic.
2. **Re-run the pilot at the corrected geometry** with a budget long enough to contain a
   real recovery phase, and see whether Deficit P recovers when it is actually given the
   chance. Until that is known, the negative control is unproven and no grid should run.
3. **Redefine the budget criterion.** "Plateaued" is unreachable under a log law; see
   below. Whatever replaces it goes in writing before `T` is chosen, not after the curves
   have been looked at.
4. **Apply the Section 7.4 budget gate** and declare the wall-clock ceiling, which still
   does not exist.
5. ~~Verify the bibliographic identifiers.~~ Done 2026-08-06; it turned up two papers absent
   from the draft, both now in Section 2.1, both narrowing the claim.

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

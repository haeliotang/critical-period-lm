# Study status

**Updated:** 2026-08-06
**Design version:** `v2-draft`
**Lifecycle state:** `DESIGN-V2-DRAFT; LADDER-1-RUNNING; PRE-FREEZE`
**Authorized next action:** read out ladder 1 and apply the registered extension rule if it
fires. No registered training run is authorized.

The registered design, the claim register, the two deficits, the decision rules, the corpus
pipeline, the model, and the trainer all exist. `make check` passes: 83 tests, including the
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

## Calibration run 2: the convergence gate, under cosine decay to zero

One clean baseline, 5,400 steps, seed 0, evaluated every 200 steps to resolve the tail.
The design response to the recovery asymmetry was to anneal the learning rate to exactly
zero at `T_total`, making convergence a property of the schedule rather than of the
absolute step count. The gate in Section 8.1 is whether the baseline improves by less than
one margin over its final 10%.

| | Decay to 0.1× peak | Decay to zero |
| --- | --- | --- |
| Improvement over final 10% | 0.0275 predicted | **0.0013 measured** |
| Against the 0.0108 margin | 2.5 margins — fails | an eighth of a margin — **passes** |
| Final validation loss | 2.0208 | 2.0406 |

Tail increments: 5,000 → 5,200 is 0.0011, 5,200 → 5,400 is 0.0002. The curve is genuinely
flat at the end rather than merely slow.

The gate is bought at a cost: final loss is 0.0198 nats worse, about two margins. Annealing
to zero means a lower average learning rate and so less total progress. That is the right
trade here — the study is not competing on absolute loss, and without convergence the
primary contrast is not interpretable at any loss.

**Consequence for the budget.** Because convergence now follows the schedule and not the
step count, a 5,400-step run converges at 5,400 steps. A scaled-down pilot is therefore a
valid rehearsal of a full-budget study rather than a truncated one, and pilot 2 costs 5.4
hours instead of 21.

## Pilot 2: complete, invalid, decisive about the control

14 runs at 5,400 steps, corrected geometry, cosine to zero. Verdict `DESIGN_FAILURE` — the
negative control scarred again. Archived under `calibration/archive/`.

| Condition | n | Delta vs baseline | p | Verdict |
| --- | --- | --- | --- | --- |
| `shuffle_early_N4` | 3 | **+0.0027** | 0.107 | **RECOVERED** |
| `permute_early_N4` | 3 | +0.0324 | 0.018 | SCAR |
| `shuffle_late_N4` | 3 | +0.0367 | 0.018 | SCAR |

Baseline 2.0401, seed SD 0.0030, margin at the 0.0100 floor. Primary contrast −0.0341
(p = 1.000): late worse than early again.

The gaps had stopped closing. All four conditions ended with the same tail slope
(0.0013–0.0016 nats over the last 400 steps) and the deficit-to-baseline gaps moved by
−0.0002 or less over that span. The measurement machinery works and the differences are
stable; what they mean is the question.

### Three findings, and three changes

**1. Deficit P is not a valid control — refuted, not doubted.** `permute_early` and
`shuffle_early` share onset and duration exactly and differ only in deficit type, and the
"harmless" one left twelve times the damage. With tied embeddings a vocabulary permutation
invalidates the input and output interface rather than perturbing the input. Replaced by
Deficit F, the same window reordering as Deficit S but with a fixed, invertible permutation.
See `deviations/2026-08-06-negative-control-replaced.md`.

**2. The claim that a scaled-down pilot rehearses the full study was false.** `warmup_steps`
was a fixed 500, so it covered 100% of the early deficit at pilot scale and 16% at full
scale; the LR-weighted disturbance during the deficit differed between arms by 2.28× at
pilot scale against 0.92× at full. `shuffle_early` recovering perfectly may say only that
its deficit landed while the model was barely learning. Warmup is now 2% of `T_total`. See
`deviations/2026-08-06-warmup-made-proportional.md`.

**3. Annealing to zero buys convergence by forcing it.** When the learning rate reaches zero
every condition stops moving, including one that had not finished recovering, so convergence
cannot by itself separate a scar from a deficit frozen in place. The late arm's gap
trajectory (0.107 → 0.053 → 0.039 → 0.037 → 0.037) decelerates smoothly rather than being
cut off, which is mildly reassuring, but decay causes smoothing too and the two are not
separable from one run. Registered response: the budget-doubling diagnostic, Section 8.2.

## Pilot 3 and the budget-doubling diagnostic: the endpoint does not survive

14 runs at 5,400 steps with proportional warmup and Deficit F as the control, then baseline
and `shuffle_late_N4` again at 10,800. Verdict `DESIGN_FAILURE`: the control scarred again.

| Condition | n | Delta vs baseline | p | Verdict |
| --- | --- | --- | --- | --- |
| `fixed_early_N4` (control) | 3 | **+0.0516** | 0.018 | SCAR |
| `shuffle_early_N4` | 3 | +0.0441 | 0.018 | SCAR |
| `shuffle_late_N4` | 3 | +0.0333 | 0.018 | SCAR |

Baseline 2.0369, seed SD 0.0068, margin 0.0204. Primary contrast +0.0108 at p = 0.0500 —
the registered direction for the first time, but below the margin.

### The diagnostic fired on first use

| | `shuffle_late_N4` gap to baseline |
| --- | --- |
| `T_total` = 5,400 | +0.0370 |
| `T_total` = 10,800 | +0.0213 |

The gap fell by 42% on one doubling — a factor of 0.58, where a permanent scar would give
1.00. Baseline loss itself went 2.0307 to 1.8544, so nothing is close to finished at 5,400
steps. **What every pilot so far has scored as permanent damage is substantially unfinished
recovery, frozen in place when the learning rate reached zero.**

Extrapolating the observed factor: 0.012 at 21,600, 0.007 at 43,200, 0.004 at 86,400. That
is the signature of a lag decaying toward nothing, not of a scar.

### The scaled-pilot claim is retracted, not repaired

Design version v1.2 claimed a scaled-down run rehearses a full-budget study; v1.3 repaired
the claim by making warmup proportional and asserted it again. It is wrong a second time,
and for a different reason: **recovery consumes an absolute amount of training, not a
fraction of the budget.** Annealing makes a short run converge, but it converges to a state
that still contains unfinished repair. Scale-invariant treatment geometry is necessary and
not sufficient. The claim is withdrawn rather than repaired a third time.

### The control failed again, and worse than the treatment

Deficit F left more damage than Deficit S at the same onset and duration (+0.0516 against
+0.0441). Two controls, two refuted predictions. The parsimonious reading is the one above:
at this budget nothing recovers, so no control can. A second, weaker hypothesis is that a
*fixed* permutation is learnable, so the model commits to a wrong but consistent grammar and
must then unlearn it, whereas a resampled permutation is unlearnable and is partly ignored.
If that holds, the axis a control must vary is commitment, not invertibility. It is a
hypothesis; it has not been tested.

### Cost of the warmup fix

Shortening warmup from 500 steps to 108 doubled baseline seed variance: SD 0.0030 to 0.0068,
margin 0.0100 to 0.0204. Same budget, same everything else. The instrument is half as sharp
as it was, and the warmup fraction is now itself a tuning question.

## Design v2: the endpoint is now a decay

The primary endpoint moved from a loss difference at one budget to the slope of that
difference against log budget, measured across a ladder. Recorded in
`deviations/2026-08-06-endpoint-changed-to-decay.md`. Consequences already applied:

- budget is a treatment variable, so the v1.3 gate requiring identical `T_total` across runs
  is gone — it would have failed every valid ladder;
- the decay test permutes budget labels; a paired sign-flip test at three seeds bottoms out
  at p = 0.125 and could never reject at 0.05;
- per-condition verdicts are `TRANSIENT`, `PERSISTENT`, `DECAYING_UNRESOLVED`, `NO_EFFECT`;
  `PERSISTENT` means survived this ladder and is always reported with the top rung;
- "the control recovers" is finally checkable: it means the control's gap decays below the
  margin;
- the duration sweep is deferred, since a ladder multiplies run count by the rung count.

The rehearsal gate was rerun against the new rules on fabricated ladders with planted shapes
and returns all four study verdicts correctly. 83 tests pass.

## Ladder 1: running

Base 2,700, rungs 2,700 / 5,400 / 10,800. Fourteen runs per rung: 3 baseline, 3
`fixed_early_N4`, 4 each for the two primary arms. About 18.5 hours.

The registered extension rule (Section 5.2) fires if the top rung leaves either the control
or the early arm at `DECAYING_UNRESOLVED`: one further rung at 21,600, about 21 hours more.
The rule was written down before the ladder started, triggers on resolution alone, and
permits at most one extension.

Expectation from the pilot 3 diagnostic, recorded so it can be checked against the outcome:
the observed decay factor was 0.58 per doubling, which would put the late-arm gap near 0.021
at 10,800 and 0.012 at 21,600 against a margin of 0.010 to 0.020. A three-rung ladder is
therefore more likely than not to return `DECAYING_UNRESOLVED` and trigger the extension.

## What still has to happen before the freeze

1. **Read out ladder 1**, and apply the extension rule if it fires.
2. **Choose the registered base budget** and re-check the Section 8.1 convergence gate at
   the top rung.
3. **Declare the wall-clock ceiling**, which still does not exist.
4. **Re-measure the budget table.** Every figure in it predates the schedule change.

## Known open design questions

- No negative control has yet decayed away, under two definitions — but neither has been
  tested under an endpoint that could have detected decay.
- The late-arm onset is fixed at `0.5T` by fiat.
- Post-deficit learning-rate area is 51% for the late arm at both scales; in a fixed-budget
  design "later" and "less recovery remains" may be the same fact rather than a separable
  confound. The ladder does not resolve this; it measures each arm's own decay.
- Whether a window shuffle at the BPE-token level is a lower-level deficit than intended.
- The warmup fraction now trades pilot validity against seed noise: shortening it from 500
  fixed steps to 2% doubled baseline seed SD at 5,400 steps.

This file is a mutable operational pointer and is not part of the freeze corpus.

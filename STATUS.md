# Study status

**Updated:** 2026-08-13
**Design version:** `v5` (frozen); v4 result final and reported
**Lifecycle state:** `V4-INCONCLUSIVE-FINAL; V5-COMPLETE; REVERSE-ONSET-EFFECT`
**Authorized next action:** write up both registered results together. No further run is
needed for the registered claim.

The registered design, the claim register, the two deficits, the decision rules, the corpus
pipeline, the model, and the trainer all exist. `make check` passes: 93 tests, including the
Section 7.2 rehearsal gate, in which the frozen decision code returns each of its four
verdicts against a planted ground truth.

**The design is frozen** at `v4`, six bound files, tag `cplm-design-v4-frozen`.
`make freeze-check` verifies the manifest; any edit to a bound file now fails it.

Every number under `calibration/` is exploratory: ladders 1 and 2 and three earlier pilots
were produced before the freeze and cannot support any claim in `CLAIMS.md`.

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

## Ladder 1: complete, and the answer is lag-shaped

42 runs across 2,700 / 5,400 / 10,800. Verdict `NO_CRITICAL_PERIOD`. Archived under
`calibration/archive/ladder1/`.

| Condition | 2,700 | 5,400 | 10,800 | slope | p | verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `fixed_early_N4` | +0.1070 | +0.0559 | +0.0229 | −0.0421 | 0.0006 | DECAYING_UNRESOLVED |
| `shuffle_early_N4` | +0.0957 | +0.0483 | +0.0221 | −0.0368 | 0.0006 | DECAYING_UNRESOLVED |
| `shuffle_late_N4` | +0.0644 | +0.0376 | +0.0218 | −0.0213 | 0.0006 | DECAYING_UNRESOLVED |

Baseline seed SD 0.0021 at the top rung, so the margin sits at the 0.0100 floor. Primary
contrast +0.0003 nats, p = 0.5000, MDE 0.0100 — onset made no detectable difference at a
resolution equal to the margin.

**The decay is the 1/T signature of a pure lag.** Factors per doubling: 0.52/0.41,
0.51/0.46, 0.58/0.58. A permanent scar predicts 1.00; a lag whose cost is fixed predicts
0.50. Every condition sits at the lag prediction.

**All three conditions converge to the same gap.** They start 0.107 / 0.096 / 0.064 and end
0.0229 / 0.0221 / 0.0218 — within 0.001 of each other. The residual is a property of *some
corruption having happened*, not of which corruption or when.

**The wound's cost is strongly sublinear in its length.** Converting gap to effective
training steps lost (`Δ_eff = T·gap/b`, with `b` estimated locally from the baseline
rungs), quadrupling the wound from 200 to 800 steps raises the cost by roughly a third:

| Condition | wound 200 | wound 400 | wound 800 |
| --- | --- | --- | --- |
| `fixed_early_N4` | 778 | 814 | 968 |
| `shuffle_early_N4` | 696 | 703 | 935 |
| `shuffle_late_N4` | 469 | 546 | 924 |

Damage behaves closer to a fixed startup cost of order 700–1,000 effective steps than to
anything proportional. `b` is not constant across rungs (0.371 then 0.255) so the levels
carry real uncertainty; the sublinearity does not depend on that, since the gap halved per
doubling while the wound doubled.

**This retires the v2 confound.** The worry in `drafts/v3-wsd-design.md` was that a
wound-proportional lag would produce a flat gap and be indistinguishable from a scar. A flat
gap is factor 1.00; the data show 0.41–0.58. The alternative is refuted empirically, so v3
is a confirmatory sharpening rather than a prerequisite for reading this result.

### Two defects in the instrument, found in this readout

**Seed plan cannot pair.** The Section 4.3 table gives the baseline 3 seeds and the primary
arms 4, while Section 5.1 pairs gaps by seed. Seed 3 of both shuffle arms therefore had no
partner at any rung: 6 runs trained and contributed nothing, about 2.6 hours, and the
primary contrast ran at 3 versus 3 (permutation floor 0.05) instead of the intended 4 versus
4 (floor 0.014). The baseline must carry every seed any deficit arm uses.

**The crossing-budget extrapolation uses the wrong functional form.** `ladder_verdict` fits
gap linearly in log budget, which on this data predicts *negative* gaps at 21,600 — the
model is not merely imprecise, it is the wrong shape. Against the 1/T behaviour the data
show:

| Condition | crossing, log-linear | crossing, 1/T |
| --- | --- | --- |
| `fixed_early_N4` | 12,710 | 24,705 |
| `shuffle_early_N4` | 12,695 | 23,880 |
| `shuffle_late_N4` | 14,943 | 23,587 |

The reported figure is optimistic by about a factor of two, and the registered extension
rung was sized by it.

### The extension rule fired, and the rung it names is too small

Both `fixed_early_N4` and `shuffle_early_N4` returned `DECAYING_UNRESOLVED`, so the
Section 5.2 rule fires: one rung at 21,600, about 21 hours. Under 1/T the predicted gaps
there are 0.0114 / 0.0111 / 0.0109 against a margin of 0.0100 — all still above it. The
extension would most likely return `DECAYING_UNRESOLVED` again, and the rule permits only
one extension, so that would become the study's final answer. Resolution needs roughly
43,200 steps.

## Design v3: the endpoint estimates a decay exponent

The endpoint moved from a categorical verdict on gap level to an estimate of how fast the
gap decays: `gap(T) = c / T^alpha`, fitted per seed, with `alpha` the reported quantity.
Recorded in `deviations/2026-08-08-endpoint-changed-to-decay-exponent.md`.

`alpha = 1` is exactly what lost training alone predicts, `alpha = 0` is no decay at all,
and the reading depends on no threshold this study chose. That is the point: the previous
endpoint made every outcome hinge on an arbitrary 0.01-nat floor, and under a power-law
decay nothing is ever exactly zero.

Applied to ladder 1's data as an exploratory check, the new endpoint reads:

| Condition | alpha | 95% interval | reading |
| --- | --- | --- | --- |
| `fixed_early_N4` (control) | 1.110 | [0.983, 1.237] | LAG |
| `shuffle_early_N4` | 1.057 | [0.780, 1.334] | LAG |
| `shuffle_late_N4` | 0.781 | [0.728, 0.833] | SUBLINEAR |

**The control lands on 1 for the first time.** That is what the design predicts of it, and
three previous controls under two previous endpoints all failed. The late arm's interval
excludes 1 — late damage outlasts the training it cost, while early damage does not.

Verdict on ladder 1 under the new rules: `INCONCLUSIVE`, and the reason is the seed defect
below, not the data.

### Five seeds is a requirement, and ladder 1 proves why

The two-sided exact permutation test has a smallest attainable p-value fixed by seed count
alone:

| Seeds per arm | One-sided floor | Two-sided floor |
| --- | --- | --- |
| 3 | 0.050 | **0.100 — cannot reject at 0.05, whatever the effect** |
| 4 | 0.014 | 0.029 |
| 5 | 0.004 | 0.008 |

Ladder 1 gave the primary arms four seeds and the baseline three. Gaps pair by seed, so the
fourth seed was unpairable at every rung: six runs trained and bought nothing, and the
effective sample fell to three. The exponent difference of +0.276 against a margin of 0.153
then returned `INCONCLUSIVE` at p = 0.100 — the floor. **The seed-plan defect cost exactly
the power needed to detect what the data were pointing at.**

The registered plan is now five seeds for every condition, and the baseline must carry every
seed index any deficit arm uses. That requirement is in Section 4.3 and is a design-failure
condition in Section 7.3.

### Other consequences applied

- A new verdict `REVERSE_ONSET_EFFECT` names late damage outlasting early damage. Its
  provenance is recorded in `CLAIMS.md` C4: ladder 1 motivated the name, and the registered
  study is what would supply evidence for it.
- The exponent margin is self-calibrating from the control's own seed spread. The nat floor
  survives only to decide whether a condition did any damage worth modelling.
- The crossing budget is computed from the power law; the retired log-linear form predicted
  negative gaps one rung out and understated it roughly twofold.
- A seed whose gap goes non-positive at any rung is dropped and reported, never nudged into
  the logarithm.
- The report now surfaces runs dropped for want of a baseline partner, which Section 5.1
  always required and the driver never did.

The rehearsal gate was rerun on fabricated ladders with planted exponents and returns all
five study verdicts correctly. 93 tests pass.

## Ladder 2: complete, and the anchor is what failed

60 runs, 5 seeds, rungs 2,700 / 5,400 / 10,800. Verdict `DESIGN_FAILURE`. Archived under
`calibration/archive/ladder2/`. Every deficit run paired — the seed-plan defect is gone.

| Condition | 2,700 | 5,400 | 10,800 | alpha | 95% interval | reading |
| --- | --- | --- | --- | --- | --- | --- |
| `fixed_early_N4` (control) | +0.1067 | +0.0506 | +0.0220 | 1.139 | [1.015, 1.262] | UNDETERMINED |
| `shuffle_early_N4` | +0.0986 | +0.0475 | +0.0201 | 1.162 | [0.855, 1.470] | LAG |
| `shuffle_late_N4` | +0.0646 | +0.0373 | +0.0222 | 0.770 | [0.743, 0.796] | SUBLINEAR |

The control's interval excludes 1 from above, by 0.015, so the Section 5.7 gate fired and
suppressed the primary contrast.

### The anchor `alpha = 1` is wrong, and the data say by how much

`gap(T) = b·Δ/T`, hence `alpha = 1`, holds only if the learning curve's log-slope `b` is
constant. It is not. Measured on the baseline rungs:

| Interval | `b` |
| --- | --- |
| 2,700 → 5,400 | 0.3688 |
| 5,400 → 10,800 | 0.2586 |

`b` falls 30% per doubling. Correcting the derivation,
`alpha_lag = 1 − dlog(b)/dlog(T) = 1.512`. Under that anchor the control at 1.139 is
*below* the pure-lag rate; under the registered anchor of 1.000 it is above. **Two
incompatible readings from the same number, decided entirely by which anchor is assumed** —
which is the signal that the anchor should not be theoretical at all.

### The control is the anchor. That is what a negative control is for.

Reading each condition against the control rather than against theory absorbs the falling-`b`
systematic and anything else the measurement does to every condition alike:

| Contrast | Difference | Two-sided p |
| --- | --- | --- |
| `shuffle_early_N4` − control | +0.023 | 0.8651 |
| `shuffle_late_N4` − control | −0.369 | 0.0079 |

Early damage is indistinguishable from the control. Late damage is not.

### The primary contrast, suppressed by the gate

`alpha(early) − alpha(late) = +0.392`, two-sided p = 0.0079 — the 5-versus-5 floor. It
depends on no anchor, being a difference of two exponents. Ladder 1 saw +0.276 at three
seeds and could not reject; the five-seed plan resolved it.

### A precision limit worth naming

At the top rung the gap is ~0.022 against a baseline seed SD of 0.0043 — a ratio of five.
Log-space fitting turns top-rung noise into exponent noise, and the rung that carries the
most information about decay is the one where the gap is smallest.

Baseline seed 4 at 10,800 is the worst of the five (1.8648 against 1.8559 for the others).
Gaps at that seed compress accordingly, and two exponent outliers follow: control 1.300
against 1.098 for seeds 0–3, and `shuffle_early` 1.582 against 1.057.

**Sensitivity check, post-hoc and labelled as such.** Dropping seed 4 entirely: control
1.098 [1.022, 1.175], early 1.057 [0.913, 1.202], late 0.773 [0.737, 0.810]; early − late
+0.284 at p = 0.0286; early − control −0.041 at p = 0.54. Every conclusion survives. This
is a robustness note, not the analysis; no seed is excluded from any reported result.

## Design v4: frozen

The control is the anchor. Readings are `LIKE_CONTROL` / `SLOWER_THAN_CONTROL` /
`FASTER_THAN_CONTROL` against the control's own fitted exponent, never against a theoretical
value. A control far from `alpha = 1` is the anchor, not a failure — the v3 rule that failed
ladder 2 for exactly that was wrong. Recorded in
`deviations/2026-08-10-control-becomes-the-anchor.md`.

**The absolute question is dropped.** Whether damage is a lag or a scar needs `Δ_eff`
estimated across rungs, and three rungs cannot pin it down. Section 3.2.1 declares it out of
scope and `CLAIMS.md` forbids pressing any exponent into service for it. What remains is
comparative and anchor-free.

Applied to ladder 2's data as an exploratory check, the frozen rules read:

| Condition | alpha | vs control | p | reading |
| --- | --- | --- | --- | --- |
| `fixed_early_N4` | 1.139 | anchor | — | ANCHOR |
| `shuffle_early_N4` | 1.162 | +0.023 | 0.8651 | LIKE_CONTROL |
| `shuffle_late_N4` | 0.770 | −0.369 | 0.0079 | SLOWER_THAN_CONTROL |

Verdict `REVERSE_ONSET_EFFECT`, primary contrast +0.392 at two-sided p = 0.0079. **This is
exploratory and supports no claim.**

Frozen at design `v4`, manifest `freeze-manifest.json`, six bound files, tag
`cplm-design-v4-frozen`. `make freeze-check` verifies; the trainer will now start registered
runs and the report driver will produce a registered verdict.

## Registered ladder: complete. Verdict `INCONCLUSIVE`.

60 runs, seeds 5–9, rungs 2,700 / 5,400 / 10,800, under the frozen `v4` rules. Records in
`runs/`, report in `results/registered/`. Every deficit run paired; no run dropped.

| Condition | 2,700 | 5,400 | 10,800 | alpha | 95% interval | vs control | p | reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fixed_early_N4` | +0.1045 | +0.0447 | +0.0196 | 1.227 | [1.020, 1.434] | anchor | — | ANCHOR |
| `shuffle_early_N4` | +0.1007 | +0.0459 | +0.0195 | 1.193 | [1.076, 1.310] | −0.034 | 0.7460 | LIKE_CONTROL |
| `shuffle_late_N4` | +0.0633 | +0.0387 | +0.0222 | 0.756 | [0.744, 0.767] | −0.472 | 0.0079 | UNDETERMINED |

Primary contrast: `alpha(early) − alpha(late) = +0.438`, two-sided p = 0.0079, one-sided p
(critical-period direction) = 1.0000. Exponent margin 0.501.

**The verdict is `INCONCLUSIVE` because the margin exceeds the difference.** This is the
registered rule applied as written. It has not been re-analysed and will not be.

### The effect replicated out of sample. The verdict did not.

| | Seeds | Delta | Two-sided p | Margin | Verdict |
| --- | --- | --- | --- | --- | --- |
| Ladder 2 (exploratory) | 0–4 | +0.392 | 0.0079 | 0.298 | `REVERSE_ONSET_EFFECT` |
| Registered | 5–9 | +0.438 | 0.0079 | 0.501 | `INCONCLUSIVE` |

The point estimate reproduced closely and the permutation test sat on its 5-versus-5 floor
in both. What moved was the margin.

**This is what the fresh-seed rule bought.** Had the registered ladder reused seeds 0–4 it
would have returned `REVERSE_ONSET_EFFECT` and the freeze would have certified a result that
a genuine out-of-sample replication does not support. Section 8.3 existed for exactly this
and it earned its place.

### Why the margin moved

The margin is `3 × SD` of the control's per-seed exponents — the control's own noise sets
what counts as a real difference. Its five exponents were 1.075, 1.160, 1.149, 1.247 and
**1.505**. The outlier belongs to seed 9, whose top-rung gap was 0.0124 against 0.0184–0.0276
for the others, because that seed's baseline at 10,800 was the worst of the five. One seed
roughly doubled the margin, from about 0.25 to 0.501.

**This is the limitation that was written into the freeze in advance.** The carried
limitations named top-rung precision — the gap there is only about five times the baseline
seed SD, and log-space fitting turns top-rung noise into exponent noise — and cited the
identical mechanism seen in ladder 2. The study documented its own failure mode before the
run and then hit it.

Note the asymmetry in precision: `shuffle_late_N4`'s exponents scatter by 0.009 across seeds
while the control's scatter by 0.167. The quantity that decides the margin is the noisiest
one in the design.

### What the registered run does establish

- `shuffle_early_N4` reads `LIKE_CONTROL` (−0.034, p = 0.746): early damage is repaired at
  the same rate as an information-preserving deficit of the same size and onset.
- `shuffle_late_N4`'s exponent is 0.756 [0.744, 0.767], tightly determined.
- The instrument behaved: control fitted, all seeds paired, no runs dropped, baseline seed
  SD 0.0029 at the top rung.

### What it does not establish

That onset changes the repair rate. The difference is large and the permutation test is at
its floor, but the registered margin — set by the control's own scatter — is larger still.
Under `CLAIMS.md` C1 and C3 this is an inconclusive result reported with the margin it was
weighed against, not a null and not a finding.

## Design v5: frozen. Instrument improved, judgment untouched.

`decision_rules.py` is **byte-identical** between v4 and v5
(`0dd42ed5566b838e…`, checkable in both manifests). The margin formula, readings, verdicts
and primary contrast are exactly what they were before the v4 result was seen. v5 spends
compute rather than credibility: the cheaper fix — pooling the scale across conditions —
would have changed a decision rule after seeing the result it disfavoured.

| | v4 | v5 |
| --- | --- | --- |
| Rungs | 2,700 / 5,400 / 10,800 | **1,350** / 2,700 / 5,400 / 10,800 |
| Seeds | 5 (indices 5–9) | **8** (indices 10–17) |
| Decision rules | frozen | **unchanged, same hash** |
| Sample SD relative error | ±34% | ±26% |
| Two-sided permutation floor | 0.008 | 0.00016 |

The fourth rung is **below**, not above: at the top rung the gap is 0.020 against a baseline
seed SD of 0.0029, so extending upward would push it further into the noise. At 1,350 the
gap is near 0.20. Registered risk: the power law may not hold that early, so the exponent is
reported both with and without the low rung, and a disagreement between them is a finding.

Frozen at tag `cplm-design-v5-frozen`. Records go to `runs/v5/`, report to
`results/registered/v5/`. The v4 evidence is untouched at `runs/v4/` and
`results/registered/v4/`.

## v5 registered ladder: complete. Verdict `REVERSE_ONSET_EFFECT`.

128 runs, seeds 10–17, rungs 1,350 / 2,700 / 5,400 / 10,800, under frozen `v5` rules whose
judgment code is byte-identical to `v4`. Records at `runs/v5/`, report at
`results/registered/v5/`. Every deficit run paired; none dropped.

| Condition | 1,350 | 2,700 | 5,400 | 10,800 | alpha | 95% interval | vs control | p | reading |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fixed_early_N4` | +0.2106 | +0.1030 | +0.0434 | +0.0197 | 1.158 | [1.068, 1.248] | anchor | — | ANCHOR |
| `shuffle_early_N4` | +0.2091 | +0.1019 | +0.0467 | +0.0190 | 1.155 | [1.085, 1.225] | −0.003 | 0.9524 | LIKE_CONTROL |
| `shuffle_late_N4` | +0.1097 | +0.0643 | +0.0381 | +0.0224 | 0.763 | [0.744, 0.782] | −0.395 | 0.0002 | SLOWER_THAN_CONTROL |

Primary contrast `alpha(early) − alpha(late) = +0.392`, two-sided exact permutation
p = 0.00016 (the 8-versus-8 floor), against a margin of 0.323. One-sided p in the
critical-period direction: 1.0000.

**Early damage repairs at the control's rate to three decimal places** (−0.003, p = 0.95).
Late damage does not (−0.395, p = 0.0002).

### Section 4.3 registered obligation: the fit with and without the low rung

| Condition | Four rungs (registered) | Three rungs (2,700 up) | Difference |
| --- | --- | --- | --- |
| `fixed_early_N4` | 1.158 [1.068, 1.248] | 1.201 [1.113, 1.290] | −0.044 |
| `shuffle_early_N4` | 1.155 [1.085, 1.225] | 1.214 [1.096, 1.332] | −0.059 |
| `shuffle_late_N4` | 0.763 [0.744, 0.782] | 0.761 [0.733, 0.789] | +0.002 |

Both fits clear the margin at p = 0.00016; the delta is +0.392 on four rungs and +0.453 on
three. **The low rung is not driving the result.** The registered risk — that the power law
might not hold at 1,350 steps — did not materialise, and the obligation is discharged with
agreement rather than with a finding.

### The instrument change did what it was for

| | v4 | v5 |
| --- | --- | --- |
| Control per-seed scatter | SD 0.1669 | SD 0.1078 |
| Exponent margin | 0.501 | 0.323 |
| Two-sided permutation floor | 0.008 | 0.00016 |

The margin fell because the control's exponents stopped scattering, which is what the fourth
rung and the extra seeds were bought to do. **No decision rule changed** — the hashes match.

### The effect across three independent seed sets

| Run | Seeds | Δ | Margin | Verdict |
| --- | --- | --- | --- | --- |
| Ladder 2 (exploratory) | 0–4 | +0.392 | 0.298 | `REVERSE_ONSET_EFFECT` |
| v4 registered | 5–9 | +0.438 | 0.501 | **`INCONCLUSIVE`** |
| v5 registered | 10–17 | +0.392 | 0.323 | `REVERSE_ONSET_EFFECT` |

The effect estimate is stable across seed sets that share no runs. What moved between v4 and
v5 was the instrument's precision, not the measurement.

## What may now be claimed, and what may not

**May be claimed** (`CLAIMS.md` C4, and C1 in its comparative form): at this scale, corpus
and schedule, damage from a window-shuffle deficit applied at mid-training is repaired more
slowly than the same deficit applied at the start, while the early deficit is repaired at the
same rate as an information-preserving control. Onset matters, in the direction **opposite**
to every critical-period account.

**May not be claimed.** That the damage is permanent, or a lag — that question is out of
scope and no exponent here may be pressed into service for it. Anything about larger models,
production pretraining, other deficits, other schedules, or human development.

**Provenance, which must travel with the claim.** The `REVERSE_ONSET_EFFECT` verdict was
added to the register *after* ladder 1 pointed at the pattern; `CLAIMS.md` C4 records the
ordering. The registered evidence for it is v5, and the v4 `INCONCLUSIVE` is part of that
record, not a discarded attempt.

## Reporting obligation, standing

Any write-up carries **both** registered results: v4 `INCONCLUSIVE` with its diagnosed cause,
and v5 `REVERSE_ONSET_EFFECT`. An improved instrument that returns a cleaner answer is a
normal scientific outcome; an improved instrument presented without the first answer is not.

## Robustness exhibit: how much of each verdict was the analysis choice

`results/robustness/{v4,v5}/multiverse.md`, produced by `make robustness`. **Enumerated
after both registered verdicts were known.** It is not a result and does not revise one;
the frozen cell of the grid reproduces the registered verdict in both cases, which is what
makes the shares interpretable at all.

144 defensible specifications: four sources for the margin's scale × three multiples of it ×
three floors × two exponent estimators × two rung sets. The verdict logic does not vary.

| Registered run | Verdict | Specifications agreeing | Dissent |
| --- | --- | --- | --- |
| v4 | `INCONCLUSIVE` | 90 / 144 (**62%**) | `REVERSE_ONSET_EFFECT` × 54 |
| v5 | `REVERSE_ONSET_EFFECT` | 138 / 144 (**96%**) | `INCONCLUSIVE` × 6 |

**This is the quantitative form of what the v4 entry says in prose.** More than a third of
reasonable analysts would have called v4 a positive result; the verdict turned substantially
on where the margin's scale came from — 83% agreement under the frozen control-only scale
against 33% under a scale pooled across the two contrasted arms. v5 is not like that: its
only dissent comes from the widest margin taken from the noisiest scale source, and every
other dimension is unanimous.

Four specifications are **excluded by name with reasons** rather than swept in: unpaired
gaps, nudging non-positive gaps into the logarithm, anchoring the exponent on the refuted
theoretical value 1, and dropping the outlier seed. Including options already known to be
wrong lets bad pipelines vote, and a spread manufactured that way says nothing.

## Limitations, unchanged

- The t-interval on `alpha` is a normality assumption; the primary contrast does not rest on
  it and is an exact permutation test.
- The power law is fitted over an 8× budget range and is an extrapolation outside it.
- The late-arm onset is fixed at `0.5T` by fiat. **The mechanism behind the effect is not
  identified and none is claimed.**
- The absolute lag-versus-scar question remains out of scope.
- `drafts/v3-wsd-design.md` and `drafts/v5-design.md` record paths not taken.

## MLX is not run-to-run deterministic, and it does not matter here

Found by `tools/branch_replay_check.py` while testing whether the trunk-branch design in
`drafts/v6-alt-wsd-design.md` is buildable. **Two runs of an identical config in separate
processes diverge** — at around step 28 in the 150-step probe — and end with different
weights. Bit-exact reproduction is unavailable on this platform to a run compared against
itself, so it was never a fair criterion for a branch.

Measured, seed 99, held-out loss:

| horizon | two straight runs | straight vs branched | ratio |
| --- | --- | --- | --- |
| 150 steps | 6.26e-07 | 1.04e-07 | 0.17 |
| 600 steps | 6.71e-08 | 1.12e-07 | 1.67 |
| **4,320 steps** (the real trunk) | **1.49e-08** | **1.86e-08** | **1.25** |

Against a baseline seed SD of 0.00235–0.00975. **The branch is no worse than repetition, and
both are five orders of magnitude below the smallest seed scatter the study resolves.**

The worry was that divergence compounds with horizon. It does not: the absolute size *falls*
with horizon, because the learning rate decays and the two trajectories are pulled together
rather than apart. Weight drift does grow (3.6e-06 at 600 steps to 7.1e-06 at 4,320) while the
held-out loss does not follow it — the weights wander inside a flat basin and the measurement
stays put.

Nothing in `results/registered/` is affected: the effects reported there are 0.02–0.21 nats.
What is affected is the wording of any claim that re-running a config reproduces a record. It
reproduces it to about **eight decimal places at the length registered runs actually are**,
not exactly, and the records were never bit-reproducible in the first place.

**Consequence for the next study:** the implementation risk in `drafts/v6-alt-wsd-design.md`
is retired, and the WSD trunk-branch design is the one to build. It is cheaper (31.6 h against
48.1 h) and it separates onset from learning-rate position instead of mapping the two
confounded.

Scope of the PASS, unchanged from what the tool prints: this machine, this MLX version, this
model, these horizons. Not established across MLX versions or hardware.

## Paper

`paper/draft.md` carries both registered results, the C4 provenance disclosure, and Section 4
as a standing scope prohibition. `paper/figures/decay-v5.{pdf,png}` is regenerated by
`make figure` from the records; it holds no number of its own.

Three corrections were made while assembling it, all in the draft and none in a result:

- **v4's two-sided p was transcribed as 0.0002; it is 0.0079.** The registered report always
  said 0.0079. Both runs' p-values sit exactly on the floor of their own permutation test
  (2/252 at five seeds, 2/12870 at eight), and the abstract's earlier claim that v4 showed
  the "same p" was wrong for that reason — the floors differ because the seed counts do.
- **Kleinman et al. moved from 2023 to ICLR 2024, Constantinescu et al. from the 2024
  preprint to the 2025 TACL volume.** `preregistration.md` carries the earlier forms and is
  deliberately not edited: a citation year is not part of the registered design.
- **Pawlak's result is on vision networks**, which the draft now states. It strengthens rather
  than weakens the scope note: our schedule never restarts the learning rate, so on that
  account it is the regime where a critical period should be most visible.

A fourth correction is larger and has its own deviation entry
([2026-08-16](deviations/2026-08-16-c4-statement-overreaches-its-own-guard.md)):
**"opposite to every critical-period account" describes no account that exists.** Achille et
al.'s onset curve is non-monotonic and peaks around a tenth of the way into their run, so a
deficit at step zero is not their worst case either; two onsets cannot recover a shape; and
their endpoint is a level where ours is a rate. `CLAIMS.md` C4 had already forbidden the
"this reverses the vision literature" reading, so the frozen register is left untouched and
only the mutable prose in `README.md` and `paper/draft.md` was corrected. **The verdict is
unaffected** — `REVERSE_ONSET_EFFECT` names a relation between two measured exponents.

`paper/arr/` is the ACL-format build of the same text, anonymized for review
(`\usepackage[review]{acl}`, official style files unmodified). `make paper` produces it and
depends on `make figure`, so the typeset paper cannot drift from the run records. **6 pages
against an 8-page limit**; Limitations and references do not count toward it.

Anonymity audited: PDF `/Author` and `/Title` empty, the figure carries only matplotlib
producer strings and no filesystem paths, and no name, handle or repository URL appears in
`main.tex` or `custom.bib`. **Three things remain and none of them is writing:** create the
anonymous repository mirror and replace the `ANONYMIZED` placeholder in §7's footnote, mirror
the working tree rather than the history (tag annotations and commit authorship carry a real
name even where file contents do not), and register with ARR as a reviewer.

**Not submitted.** BabyLM 2026 closed on 20 July (ARR commitment 14 August); the workshop is
24–29 October at EMNLP. The next open ARR cycle is **12 October 2026** (commitment 20 December,
to NAACL 2027 / COLING 2027); ARR now requires every author to register as a reviewer, with an
exemption for insufficient experience, and non-registration is a desk reject. The venue
decision is open.

This file is a mutable operational pointer and is not part of the freeze corpus.

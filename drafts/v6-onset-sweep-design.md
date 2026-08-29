# v6 design draft — the shape of the onset curve

**Date:** 2026-08-29
**Status:** draft, not registered, not authorized. No run may be started against this file.
**Relation to v5:** a new study with a new question, not a re-analysis. It reuses v5's
manipulation and machinery; it does not reuse v5's records, seeds, or verdict logic.

---

## 1. The question, and why it is now open

v5 measured the repair exponent at two onsets and found

| onset | α |
| --- | --- |
| `0.0 T` | 1.155 |
| `0.5 T` | 0.763 |

and the paper reports that as a difference. **Two points establish a difference and cannot
establish a shape**, which `paper/draft.md` §4 now says in as many words. The shape is not a
detail. Achille et al. (§2 of ICLR 2019) slide a fixed-length window across onsets and report
verbatim:

> we observe that the sensitivity to the deficit peaks in the central part of the early rapid
> learning phase (at around 30 epochs), while introducing the deficit later produces little or
> no effect.

**Their onset curve is non-monotonic.** Damage rises, peaks about a tenth of the way into
their run, then falls away. Translated into this study's endpoint — more persistent damage
means a *lower* α — an Achille-shaped curve would give α a **minimum at an interior onset and
a rise afterwards**.

v5's two points are consistent with both readings:

- **monotonic:** α keeps falling as onset moves later;
- **single-troughed:** `0.5 T` is on the descending limb and α turns back up later.

Nothing in the v5 records distinguishes them, because the design has no onset past `0.5 T`.

**The registered question of v6 is exactly that discrimination.**

## 2. What is inherited unchanged, and what is not

This matters more than the sweep itself. v5's credibility rested on `decision_rules.py`
hashing identically across two freezes; v6 cannot make that claim and must not imply it.

| Component | Status in v6 |
| --- | --- |
| `deficits.py` — Deficit S, Deficit F, window size, `steps_from_clean_budget`, the 2.16 geometry | **byte-identical.** Verified: `steps_from_clean_budget` has no upper bound on the fraction and `DeficitSchedule` requires only non-negative bounds, so onsets past `1.0 T` need no code change |
| `model.py`, `data.py`, `train.py` | unchanged |
| `decision_rules.py` primitives — `exact_permutation_p`, `fit_exponent`, `paired_gaps`, `t_interval`, `level_margin` | **reused unchanged** |
| `decision_rules.py` — `study_verdict`, `read_against_control` | **replaced.** The question is a shape across six arms, not a contrast against a control. New logic means a **new rehearsal gate**: v6's verdict function must return each of its outcomes correctly against fabricated ladders with planted onset curves before it sees a real run |

The manipulation is therefore literally the v5 manipulation, sampled at more onsets. **The
judgment is new and gets no inherited credit.**

## 3. Design

### 3.1 Onsets

Six, as fractions of the clean budget `T`. Geometry verified feasible and scale-invariant at
every rung:

| onset | deficit ends | recovery left | in v5 |
| --- | --- | --- | --- |
| `0.00 T` | `0.16 T` | 92.6% of run | ✓ early arm |
| `0.25 T` | `0.41 T` | 81.0% | new |
| `0.50 T` | `0.66 T` | 69.4% | ✓ late arm |
| `0.75 T` | `0.91 T` | 57.9% | new |
| `1.00 T` | `1.16 T` | 46.3% | new |
| `1.50 T` | `1.66 T` | 23.1% | new |

Recovery fractions are identical at 1,350 / 2,700 / 5,400 steps to within rounding (69.5% vs
69.4% at the smallest rung). **This is the property the whole design rests on:** each onset's
recovery handicap is a constant multiple across rungs, so by the amplitude-versus-exponent
argument already verified in `analysis/handicap.py`, each onset's α is uncontaminated by its
own handicap. Handicaps differ *between* onsets, which is fine, because α is what is compared
and a constant factor does not move it.

`0.00 T` and `0.50 T` are carried forward deliberately: with fresh seeds they re-measure v5's
contrast out of sample.

### 3.2 Rungs, arms, seeds

| | |
| --- | --- |
| Rungs | 1,350 / 2,700 / 5,400 steps — **the top rung is dropped** |
| Deficit S | all six onsets |
| Deficit F (control) | onsets `0.00 T` and `1.50 T` only |
| Baseline | every seed at every rung |
| Seeds | **18–25**, fresh; calibration used 0–4, v4 5–9, v5 10–17 |
| Total | 72 runs per rung, **216 runs**, ~50 h |

**Why the top rung goes.** It costs 52% of a four-rung ladder (24.4 h of v5's 46.6 h) and this
question does not need it: the discrimination is about the *ordering* of α across onsets, and
the low rungs carry the best signal — the gap is 21.6× the baseline seed SD at 1,350 and 13.4×
at 2,700, against 8.4× at 10,800. The cost is precision on each individual α, from three points
over 4× instead of four over 8×. **That is a real loss and is declared, not hidden.**

Measured alternatives, so the trade is visible rather than asserted:

| plan | runs | hours |
| --- | --- | --- |
| **A (this design)** 3 rungs, 6+2 arms, 8 seeds | 216 | **49.9** |
| B same, 6 seeds | 162 | 37.4 |
| C Deficit F at all six onsets | 312 | 72.1 |
| D add the 10,800 rung | 288 | 104.9 |
| E four onsets instead of six | 168 | 38.8 |

B is rejected: v4 died of a scale estimated from five seeds, and six is not enough of a repair.
D is rejected on cost. E is rejected because four onsets barely improve on two for a shape.
C is the one worth regretting — see §5.

### 3.3 Deficit F at two onsets is the load-bearing control

Deficit F is information-preserving, so **its α should not depend on onset at all**. If it
does, then α varies with onset for reasons that have nothing to do with destroying
information — schedule position, recovery allowance, something unmodelled — and the entire
shape result is confounded.

Running F at `0.00 T` and `1.50 T` tests exactly that, across the widest span in the design.

**This is a registered design-failure gate, not a robustness note.** See §4.3.

## 4. Endpoint

### 4.1 Primary contrast

**`Δ = α(1.50 T) − α(0.50 T)`, two-sided exact permutation test across seeds, 8 vs 8.**

One pre-specified contrast, chosen because it is precisely what v5 could not see. Two-sided
deliberately: v5 registered a one-sided direction, got `p = 1.0000` on it, and had to lean on
the secondary. **We do not know which way this goes and will not pretend to.**

Margin: three times the control's own per-seed exponent scatter, floored at 0.10 — the v5 rule
and constants, unchanged.

### 4.2 Readings

| Δ | p | verdict |
| --- | --- | --- |
| `≥ +margin` | `≤ 0.05` | `TURNS_BACK_UP` — non-monotonic; the same shape family as Achille et al. |
| `≤ −margin` | `≤ 0.05` | `STILL_FALLING` — α continues to decrease past `0.5 T` |
| `\|Δ\| < margin` | `> 0.05` | `FLAT_AFTER_MID` — the curve plateaus |
| otherwise | | `INCONCLUSIVE` |

The other four onsets are a **registered descriptive curve**, reported in full with intervals,
and are not permitted to change the verdict. Fitting a shape to six points and then testing
the shape you fitted is the failure this register exists to prevent.

### 4.3 Design-failure gates, all pre-specified

1. **Control onset-invariance.** If `|α_F(1.50 T) − α_F(0.00 T)| ≥ margin`, verdict is
   `CONTROL_ONSET_DEPENDENT` and the primary contrast is **not reported as a shape result**.
   The control moving with onset means the axis is not clean.
2. **Every arm must actually decay.** If any S arm's α is within the margin of zero, that arm
   measures "there was no time to recover", not "recovery was slow". Such an arm is excluded
   by this rule, named in the report, and if it is the `1.50 T` arm the verdict is
   `NO_RECOVERY_AT_LATE_ONSET`. **This is the most likely way v6 fails** and it is written
   down before any run.
3. **Handicap constancy, measured not assumed.** For each onset, the learning-rate-area ratio
   across rungs must vary by less than 1%. It was 0.18% for v5's late arm. Computed by the
   existing `analysis/handicap.py` machinery before the verdict is read.
4. **Baseline completeness.** The baseline must carry every seed index used by any deficit
   arm. Ladder 1 wasted six runs on this; the report already surfaces unpaired runs.

### 4.4 The v5 replication check

Onsets `0.00 T` and `0.50 T` with seeds 18–25 re-measure v5's primary contrast out of sample.
Registered expectation: `α(0.00 T) − α(0.50 T) > 0`.

**This is reported, not gated.** It cannot rescue the primary and cannot kill it. If it fails,
that is a finding about v5 and is reported as one — at three rungs rather than four, so a
smaller estimate is expected and only a sign reversal would be surprising.

## 5. What v6 still cannot answer

**Whether the damage is permanent.** Unchanged from v5, unchanged for the same reason. Out of
scope.

**Whether the curve's shape is about training time or about the learning rate.** v6 maps α as a
function of onset, and **onset still moves along the cosine schedule**, exactly as in v5. The
curve v6 recovers is the shape of the confounded function. Achille et al.'s curve is confounded
the same way (they used exponential annealing), so the comparison is like for like — but
neither isolates "when in training" from "at what learning rate".

Separating them needs a schedule with a flat trunk, which is already drafted in
[`v3-wsd-design.md`](v3-wsd-design.md). That design was shelved when a simpler ladder fix was
available. **It is now the only design in the drawer that answers the question v6 raises**, and
it should be reconsidered before v6 rather than after — if the answer is "the shape is a
learning-rate artefact", v6's curve is a description of the schedule.

**A mechanism.** No representational measure is planned here either. Adding CKA needs
checkpoints, which needs re-running everything, which is a different study.

**Any claim beyond 7.34M parameters, TinyStories, and this schedule.**

## 6. Honest assessment before committing 50 hours

Three things argue for running it:

- The question is **already written into the paper** as an acknowledged gap, so the result has
  a place to go whether it is positive or null. §4's "the shape of the onset curve" becomes a
  results subsection.
- It is the **cheapest** of the four open questions by an order of magnitude — 50 h against
  200 h+ for lag-versus-scar.
- It has an **external referent**. Achille's Figure 1C is this experiment with a level
  endpoint; running it with a rate endpoint is a clean contribution either way.

Two argue for waiting:

- **The confound in §5 may make the answer uninterpretable.** If the shape turns out to be a
  learning-rate artefact, 50 hours buys a description of the cosine schedule. Deciding whether
  to do the WSD variant *first* is the real decision, and it is not a cost question.
- Gate 2 is a genuine risk. The `1.50 T` arm has 23.1% of the run left to recover in; if its
  gap does not decay across rungs, the most informative onset in the design is the one that
  fails.

**Recommendation: do not authorize this file as written.** Resolve §5 first — decide whether
the onset axis or the schedule axis is the one worth 50 hours. If the onset axis wins, this
design is ready to be turned into a preregistration; if the schedule axis wins, `v3-wsd` is,
and v6 becomes its second study rather than its first.

## 7. Not authorized

No preregistration, no freeze, no runs. Turning this into a registered design requires, at
minimum: the new verdict function written and passing a rehearsal gate against planted onset
curves; §5 resolved; the seed plan and gates transcribed into `preregistration.md`; a new
freeze manifest and tag.

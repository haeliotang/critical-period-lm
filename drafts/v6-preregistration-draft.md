# v6 preregistration — DRAFT

**Design version:** `v6` (proposed)
**Status:** **DRAFT. Not frozen, not registered, no tag, no authorized runs.**
**Becomes `preregistration.md` only when** §9's checklist is complete. Until then
`preregistration.md` remains the v5 document and v5 remains the design of record.

Supersedes the design sketches in [`v6-alt-wsd-design.md`](v6-alt-wsd-design.md), which stays
as the argument for why this shape was chosen over
[`v6-onset-sweep-design.md`](v6-onset-sweep-design.md).

---

## 1. The registered question

v5 found that damage from a deficit at mid-training is repaired more slowly than damage from
the same deficit at the start. Under v5's cosine schedule a later onset is **also a lower
learning rate**, so that finding is a statement about one confounded axis. The v5 paper says
so in its limitations; this study is the attempt to separate them.

> **Does the repair exponent depend on deficit onset when the learning rate does not change?**

A warmup–stable–decay trunk holds the rate at its peak from step 108 to step 4,320, so two
deficits placed inside that window differ in training time by up to 35× at **one learning
rate**. That is the entire reason for the schedule.

Both answers are informative and both are registered in advance:

- **Yes** — onset does work of its own; v5's effect is not merely schedule position.
- **No** — the honest reading is that v5's effect *was* the schedule, and the limitation
  becomes the result.

## 2. What this study cannot answer

Registered before any data, and not revisable afterwards.

- **Whether damage is permanent.** Out of scope in v5 for a reason that WSD does not fix:
  recovering an effective-step debt means inverting the baseline curve, and three rungs cannot.
  **Dropped, not answered.** No exponent here may be pressed into service for it.
- **A mechanism.** None is measured and none is claimed. No representational measure is
  planned; adding one needs checkpoints at every step, which is a different study.
- **Anything about scale, corpus, or other deficits.** 7.34M parameters, TinyStories, one
  deficit pair, one peak learning rate.
- **Anything about development or cognition.** `CLAIMS.md`'s prohibition carries over intact.
- **Comparability with v4 or v5.** Those ran cosine-over-the-whole-budget. **No result here
  may be read against them as if it were the same measurement**, and the schedule is the
  reason this study exists rather than an incidental difference.

## 3. Design

### 3.1 Schedule and execution

Linear warmup over 108 absolute steps to a peak of 3e-4; constant peak through the stable
phase; cosine to exactly zero over the final 20% of each rung. One trunk per (condition,
seed), run to 4,320 steps, with complete training state checkpointed at each rung's branch
point; one decay leg per rung annealed from its checkpoint.

Two rungs therefore share a bit-identical trajectory to the shorter one's branch. **"Same
deficit, more recovery" is a construction, not an approximation**, and v5's recovery-handicap
argument holds by construction rather than by the empirical check `analysis/handicap.py` had
to perform.

| | |
| --- | --- |
| Rungs | 1,350 / 2,700 / 5,400 steps |
| Branch points | 1,080 / 2,160 / 4,320 |
| Legs | 270 / 540 / 1,080 |
| Steps per (condition, seed) | 6,210, against 9,450 as separate runs |

### 3.2 Deficits

**Unchanged from v5 and taken from the frozen `deficits.py` without modification.** Deficit S
is the resampled 16-token window shuffle; Deficit F is the same operation under a single fixed
permutation, so it is invertible and destroys nothing.

The window is **400 absolute steps at an absolute onset**, not a fraction of each rung's
budget. v5 needed fractions so the rungs would be scale-invariant copies of one another; here
the rungs share a trunk, so they are not copies — they are the same run — and an absolute
onset strikes the same model state at the same learning rate at every rung. That is stronger
than self-similarity, and it is why the fractional geometry is dropped without reopening the
defect it was introduced to fix (pilot 2's fixed warmup): there is one warmup, in one trunk.

### 3.3 Arms

| condition | onset | rate-matched |
| --- | --- | --- |
| `baseline` | — | — |
| `shuffle_0` | 0 | **no** — overlaps warmup |
| `shuffle_108` | 108 | yes |
| `shuffle_600` | 600 | yes |
| `shuffle_1400` | 1,400 | yes |
| `shuffle_2600` | 2,600 | yes |
| `shuffle_3800` | 3,800 | yes |
| `fixed_108` | 108 | yes — control |
| `fixed_3800` | 3,800 | yes — control |

**Onset 0 is registered as reported-but-excluded.** It is the theoretically interesting case
and it is v5's early arm, and it is the one onset whose deficit spans a changing learning rate.
It is reported with its exponent and interval; **it may not carry the primary contrast.**
Letting it in would give away the property the design exists for.

Deficit F sits at both extremes of the matched range because its exponent **must not depend on
onset** — it destroys nothing. If it does, α varies with onset for reasons unrelated to
information loss and the axis is not clean. That is a gate, not a robustness note (§5).

### 3.4 Seeds

**26–33.** Calibration used 0–4, v4 used 5–9, v5 used 10–17, and the v6 margin pilot uses
18–25. **The registered run may not reuse any seed spent on calibration or on a previous
registered run.** This rule earned its place in v4: had that run reused the calibration seeds
it would have returned a positive verdict a genuine out-of-sample replication does not support.

Nine conditions × 8 seeds = 72 trunks, 216 leg measurements, ~31.6 hours.

## 4. Endpoint

Per seed, per condition: gap to the seed-matched baseline at each rung, fitted as
`gap(T) = c / T^α` by OLS in log-log space. **Seeds are the replication unit** and inference is
across seeds.

**Primary contrast:** `α(earliest matched onset) − α(latest matched onset)` — that is,
`α(108) − α(3800)` — by **two-sided** exact permutation, 8 vs 8, floor `2/12870 ≈ 0.00016`.

Two-sided deliberately. v5 registered a one-sided direction, got `p = 1.0000` on it, and had to
lean on its secondary. We do not know which way this goes.

**Margin:** three times the control's own per-seed exponent scatter, floored at 0.10 — v5's
rule and constants, unchanged. **The floor's value is set by the pilot (§8) and frozen before
any registered run.**

**Second registered reading — concordance.** The primary is blind to a curve whose extremes
match and whose middle differs, which is precisely the shape Achille et al. report in vision.
So Kendall's W across the five matched onsets is registered alongside it: do the seeds agree on
an ordering? **This is a randomisation test with 20,000 draws, not an exact one — the only
inexact test in this project, and it is labelled rather than left to the word "permutation" to
imply otherwise.**

Both readings are reported always. Neither may be substituted for the other after the fact.

## 5. Verdicts and gates

Implemented in `src/critical_period_lm/wsd_decision.py`, rehearsed in
`tests/test_wsd_decision.py` against planted onset curves. The verdict function is a pure
function of the records with no discretion at any point.

**Gates, checked in order, before any primary is read:**

1. `CONTROL_ONSET_DEPENDENT` — the two Deficit F arms' exponents differ by at least the
   margin. The onset axis is confounded and **no primary is reported.**
2. `ARM_DID_NOT_DECAY` — any matched arm's exponent falls within the margin of zero. That arm
   measured "there was no time to recover", not "recovery was slow". **This is the most likely
   way the design fails and it is written down before any run.**

**Verdicts:**

| condition | verdict |
| --- | --- |
| `\|Δ\| ≥ margin` and `p ≤ 0.05` | `ONSET_EFFECT_AT_CONSTANT_RATE` |
| `\|Δ\| < margin`, `p > 0.05`, and the arms span less than the margin | `NO_ONSET_EFFECT_AT_CONSTANT_RATE` |
| `\|Δ\| < margin`, `p > 0.05`, arms span ≥ margin **and** seeds concordant | `INCONCLUSIVE` — a non-monotonic curve is not ruled out |
| margin and significance disagree | `INCONCLUSIVE` |

The third row is the registered guard, and it carries a magnitude condition on purpose: the
rehearsal gate caught that concordance alone detects arbitrarily small consistent structure, so
without requiring the arms to span at least the margin **a systematic difference of 1e-9 would
make the null unreachable forever.** That defect was found by the planted tests, before data.

## 6. Standing infrastructure gate

`make branch-check` must pass **at the registered trunk length** before the freeze, and again
if MLX or the hardware changes. Measured 2026-08-29 at 4,320 steps: branching moves held-out
loss by 1.86e-08 where running the same config twice moves it by 1.49e-08, both five orders of
magnitude below the smallest baseline seed SD.

Note what that gate is *not*: MLX is **not** run-to-run deterministic here, so no run in this
project has ever been bit-reproducible. The gate asks whether branching is worse than
repetition, which is the question that bears on the measurement.

## 7. Analysis discipline

Carried over from v5 without change: the analysis driver has no filtering and no discretion;
runs dropped for want of a baseline partner are surfaced, never silent; `deviations/` is
append-only and records whether each departure was decided before or after the affected result
was visible; the registered report refuses to run without an intact freeze.

## 8. What the pilot must supply before this can be frozen

Running now: seeds 18–25, three conditions (`baseline`, `fixed_600`, `shuffle_600`), three
rungs, ~10.5 hours. It is exploratory, written to `calibration/wsd/`, and excluded from every
claim.

1. **The control's per-seed exponent scatter**, which sets the margin. This is the number v4
   got wrong with five seeds.
2. **Confirmation that the deficit produces a measurable gap at all** under WSD — without the
   `shuffle_600` arm the pilot could not tell a small margin from nothing happening.
3. Whether any arm trips gate 2 at this geometry.
4. A throughput figure to replace the 31.6-hour estimate with a measurement.

**If the pilot shows the control's exponent scatter is large enough that the margin exceeds any
plausible effect, this design is not run as written** — that is v4's failure, and the point of
a pilot is to meet it before spending 31.6 hours rather than after.

## 9. Checklist before this becomes `preregistration.md`

- [x] Trunk-branch infrastructure implemented and tested
- [x] Branch-replay gate passing at the registered trunk length
- [x] Verdict function written and passing a rehearsal gate against planted curves
- [ ] Pilot read out; margin floor set from it
- [ ] `CLAIMS.md` rewritten for v6's claims and non-claims
- [ ] `freeze.py` bumped to `v6`, the bound file list revised, manifest rebuilt
- [ ] `make check` green, tag `cplm-design-v6-frozen` written
- [ ] Deviation entry recording what changed from v5 and why

**Nothing in this file authorizes a run.**

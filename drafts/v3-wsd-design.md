# Design v3 draft: fixed wound, WSD schedule, trunk-branch ladder

**Status: DRAFT. Not active, not frozen, not the design of record.**
The design of record is `preregistration.md` at `v2-draft`, under which ladder 1 is
currently running. This document exists so that the v3 decision, when it is made, is made
against a worked-out alternative rather than a slogan. Nothing here authorizes a run.

Adopting this draft requires: a version bump to v3, edits to `preregistration.md` and
`CLAIMS.md`, a rewrite of the schedule and trainer, a new rehearsal of the decision rules,
and a deviation entry. None of that happens before ladder 1 reads out.

---

## 1. The defect this design removes

The v2 ladder scales the deficit with the rung: 200 wound steps at budget 2,700, 400 at
5,400, 800 at 10,800. Under the measured log-shaped loss curve `loss ≈ a − b·ln(t)`, a pure
lag — the wound wasted Δ effective steps and nothing more — produces a gap to baseline of

    gap ≈ b·Δ / T.

If the lag is proportional to the wound (`Δ = k·W`) and the wound is proportional to the
budget (`W ∝ T`), the two cancel: **gap ≈ 0.074·k·b, a constant at every rung.** A flat gap
is the registered signature of a scar, so under v2 a `PERSISTENT` verdict cannot be told
apart from a wound-proportional lag. The ladder was adopted to separate scar from lag, and
scaling the wound with the rung silently removed that separation in the positive direction.
(The null direction survives: a decaying gap rules out a scar under either reading.)

The discriminating design holds the wound fixed and grows only the recovery:

| | Pure lag predicts | Scar predicts | Distinguishable? |
| --- | --- | --- | --- |
| v2: wound ∝ budget | flat gap | flat gap | **no** |
| v3: wound fixed | gap ∝ 1/T — halves per doubling | flat gap | **yes** |

A fixed wound collides with the v2 schedule: warmup is 2% of the budget, so at the top rung
(216 warmup steps) a 400-step wound sits half inside warmup while at the bottom rung it
does not — the pilot-2 defect reborn. The collision is resolved by changing the schedule,
which is the second half of this design.

## 2. Schedule: warmup–stable–decay (WSD)

- **Warmup:** linear, 0 → peak, over a **fixed absolute step count** `W_up`.
- **Stable:** constant peak learning rate.
- **Decay:** cosine from peak to exactly zero over the final `20%` of each budget.

The property that everything else buys: **two runs with different budgets share a
bit-identical trajectory until the shorter one begins its decay.** Same warmup, same wound,
same batches, same learning rate, same parameter values, step for step. "Same wound, more
recovery" stops being an approximation and becomes a construction.

Convergence at every rung is preserved: each leg still anneals to zero, so the Section 8.1
convergence gate still applies, checked per rung on the annealed leg.

v2 needed proportional warmup because it needed rung self-similarity. v3 does not need
self-similarity — it needs identical treatment — and fixed warmup provides exactly that.
Note the interaction with the Pawlak moderator (arXiv:2510.09687): the schedule is a
registered constant and a named scope limit, and **v3 results are not comparable to v2 or
to any pilot**, all of which ran under cosine-over-the-whole-budget.

## 3. Geometry: absolute steps, defined once

All quantities in optimizer steps, fixed for the whole study, identical at every rung.
Draft values, to be fixed at calibration:

| Quantity | Draft value | Constraint |
| --- | --- | --- |
| Base budget `B` | 2,700 | rungs `B, 2B, 4B`, extension `8B` |
| Warmup `W_up` | 108 | small against the wound; inside every rung's stable phase |
| Wound duration `N` | 400 | matches the rung-2 wound of v2, where effects are measured |
| Early onset | 0 | wound overlaps warmup identically at every rung |
| Late onset | 1,250 | wound must end before the first branch: `1,250 + 400 ≤ 0.8·B = 2,160` ✓ |
| Decay fraction | 0.20 | decay of rung `R` runs over `[0.8·T_R, T_R)` |

"Early" and "late" are now absolute onsets, which is what an onset contrast should have
been: the late wound strikes the same model state at every rung, because the trajectory up
to that point is shared.

## 4. Execution: one trunk, branched decay legs

Per (condition, seed):

1. **Trunk:** warmup + stable LR, wound applied at its window, run to `0.8·4B = 8,640`
   steps. Full training state (weights, AdamW moments, data-stream RNG, deficit RNG)
   checkpointed at `0.8·B`, `0.8·2B`, and trunk end.
2. **Legs:** from each checkpoint, anneal to zero over `0.2·T_R` steps. The leg's endpoint
   is that rung's registered measurement.

Cost per (condition, seed): `8,640 + 0.2·(B+2B+4B) = 12,420` steps against `18,900` for
separate runs — a 34% saving. The saving is why v3 can afford more seeds (Section 6).

The extension rung (`8B`) requires continuing the trunk from its saved end state to
`0.8·8B = 17,280` and branching one more leg. This is only possible if the trunk-end
checkpoint captures the complete state; that requirement is part of the design, not an
implementation nicety.

New obligations this creates:

- exact state serialization (MLX arrays, optimizer moments, both RNGs). Disk cost is
  trivial (~30 MB × a few checkpoints × 20 trunks);
- a leg must be bit-reproducible from its checkpoint; the test suite gains a
  branch-and-replay test;
- trunk evals every 200 steps give a continuous gap trajectory on a shared trajectory at
  constant LR — registered as a **secondary, descriptive** measure. It is the cleanest
  picture of the wound and its repair, but it is pre-anneal, so it does not replace the
  leg endpoints.

## 5. Endpoint: the lag/scar decomposition

Gap as before: `g(condition, rung, seed) = leg_loss(condition) − leg_loss(baseline)`,
paired within rung and seed.

The registered model is the sum of a lag term and a scar term:

    gap(T) = c/T + d
        c : lag, in nats·steps; Δ_eff = c/b converts it to effective steps lost
        d : asymptotic gap — the scar, in nats

which linearizes exactly:

    T·gap = c + d·T

so `d` is the slope of `T·gap` against `T`, and `c` the intercept. Per seed, the rungs of
one condition share a trunk and give one internally-paired line; each seed yields one
`(c, d)` estimate; seeds are the replication unit.

**Per-condition verdicts** (margin as in v2: `max(3·SD_baseline_top, 0.01)`):

- `TRANSIENT` — upper confidence bound of `d` below the margin: whatever remains
  asymptotically is smaller than the smallest difference the study respects.
- `PERSISTENT` — lower confidence bound of `d` at or above the margin: a scar of at least
  the margin, **at budgets up to the top rung** (always reported with it).
- `UNRESOLVED` — neither bound clears; triggers the registered extension rule, once.
- `NO_EFFECT` — gap below the margin at every rung, no trend required.

**Headline descriptive quantity:** `Δ_eff = c/b`, the wound's cost in effective training
steps. Pilot data put it at 1–2× the wound's own length. "An early corruption of length N
costs about 1.5·N effective steps and leaves no asymptotic scar" is a sharper sentence than
any scar/no-scar binary, and it is the sentence the evidence currently points toward.

**Inference, stated honestly.** With seeds as the unit, `d` is tested by a one-sample
t-interval across per-seed estimates (df = seeds − 1). That is a normality assumption at
n = 5, and it is the weakest link in this design; it is declared rather than hidden. The
nonparametric within-seed budget-label permutation (each seed's rung labels permuted
independently; `(3!)^5 = 7,776` assignments at three rungs and five seeds) is retained as
the registered check that decay exists at all. The v2-style free permutation across all
gaps is dropped: legs sharing a trunk are strongly dependent, and pretending otherwise
would be exactness theater.

**Model assumption, declared:** the `c/T` form assumes the local log-law slope `b` is
constant across the ladder's budget range. It is approximately true of the measured curve
and is checked descriptively against the baseline rungs; the nonparametric decay check does
not depend on it.

**Primary contrast:** `d_early − d_late`, paired by seed. A paired sign-flip test at four
seeds enumerates 2⁴ = 16 assignments and bottoms out at p = 0.0625 — it can never reject at
α = 0.05. **Five seeds (2⁵ = 32, floor 0.031) is therefore the minimum for the registered
paired test**, which is the second reason Section 6 sets five seeds everywhere.

**Study verdicts** keep the v2 conjunction shape: the control ladder must return
`TRANSIENT` or `NO_EFFECT` before anything else is read; `CRITICAL_PERIOD` requires a
`PERSISTENT` early arm plus a rejected paired primary contrast with `d_early − d_late ≥`
margin; `NO_CRITICAL_PERIOD` requires non-rejection at adequate resolution, with the early
arm's own `TRANSIENT`/`NO_EFFECT` verdict reported alongside.

## 6. Seeds and budget

Five seeds for every condition — baseline, `fixed_early_N4`, `shuffle_early_N4`,
`shuffle_late_N4` — 20 trunks.

| | v2 ladder (running) | v3 draft |
| --- | --- | --- |
| Seeds | 3 / 3 / 4 / 4 | 5 / 5 / 5 / 5 |
| Wall clock, three rungs | 18.5 h | **17.4 h** |
| Extension rung | +21 h | +18.1 h |
| Paired primary test possible | no (free permutation only) | yes (floor 0.031) |

The trunk sharing pays for the extra seeds with room left over. Disk and thermal notes as
before; all figures at the measured 3.97 steps/s.

## 7. What carries over from v2 unchanged

- Deficit S (resampled window shuffle) and Deficit F (fixed window permutation) and the
  question the control answers.
- The margin definition, the freeze mechanics, the append-only rules, the exploratory/
  registered separation, the analysis driver's no-discretion contract.
- The extension rule: once, on `UNRESOLVED`, decided by frozen code.
- The claim register's scope limits, including the Pawlak schedule caveat — which v3
  makes load-bearing, since v3 exists partly *because* the schedule mattered.

## 8. What ladder 1 must supply before v3 can be frozen

1. **Whether the confound bites at all:** if ladder-1 gaps fall ~0.5× per rung (lag with
   non-scaling Δ_eff), the v2 ambiguity is empirically moot and v3's role is confirmatory
   sharpening. If any gap is flat, v3 is the only way to read it.
2. Multi-seed decay factors to replace the single-seed 0.58.
3. Baseline seed SD under the current warmup, for the v3 margin forecast.
4. Whether the extension rule fires, as a rehearsal of the sequential machinery.

## 9. Open questions, carried or new

- The t-interval on `d` at n = 5 is the design's weakest inference; a preregistered
  Bayesian interval or more seeds are the alternatives, both with costs.
- Warmup length is still a free parameter; v3 removes its scale-coupling but not the
  noise-versus-validity trade observed when it was shortened.
- The late onset (1,250) is as much a fiat as v2's `0.5T`.
- Whether checkpoint-exact branching holds bit-for-bit under MLX compilation is an
  implementation risk to be retired by test before anything is registered.

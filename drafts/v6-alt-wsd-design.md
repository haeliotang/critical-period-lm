# v6 alternative — WSD trunk-branch, with onset separated from learning rate

**Date:** 2026-08-29
**Status:** draft, not registered, not authorized. No run may be started against this file.
**Relation to other drafts:** this and [`v6-onset-sweep-design.md`](v6-onset-sweep-design.md)
are **two candidates for the same next study**, not a sequence. It rewrites
[`v3-wsd-design.md`](v3-wsd-design.md), which was written before ladder 2, v4 and v5 existed
and whose endpoint has since been refuted. The original is kept unedited as a record of what
was thought at the time.

---

## 1. What changed since the original WSD draft

The original was designed to answer one question — **is the damage a lag or a scar** — and
proposed the endpoint

    gap(T) = c/T + d,   linearised as   T·gap = c + d·T

with `d` the asymptotic scar. **That endpoint is refuted.** It assumes the baseline learning
curve's local log-slope `b` is constant across the ladder, and ladder 2 measured `b` falling
about 30% per doubling (0.4861 → 0.3655 → 0.2646 across v5's rungs). This is the same defect
that killed the `α = 1` anchor and is recorded in `deviations/`. Any rewrite that carries
`c/T + d` forward is carrying a known-dead assumption.

Three other things changed:

- **v4 and v5 ran.** There are two registered results, and the endpoint of record is
  `gap(T) = c/T^α` with `α` read against the control's own measured exponent.
- **The seed count moved 5 → 8.** v4 returned `INCONCLUSIVE` because a margin estimated from
  five seeds scattered by ±34%.
- **The reason to want WSD changed.** It is no longer mainly about lag versus scar. Reading
  Achille et al. closely while writing the paper surfaced a confound that v5 and the
  cosine-schedule v6 draft both share and neither can remove.

## 2. The property that is now the point

Under the registered cosine schedule, moving the deficit window later in training also moves
it to a lower learning rate. **"When in training" and "at what learning rate" are one axis,
not two.** Every onset result this project has produced — v5's contrast, and the curve the
cosine v6 draft would map — is a statement about that single confounded axis.

This is not a hypothetical worry. \[Pawlak 2025] reports that restarting the learning rate
undoes critical-period damage in vision, and \[Luo et al. 2025] find that curriculum effects
in LLM pretraining survive under a constant learning rate and vanish under standard decay.
Both say the schedule position is doing work in exactly this class of effect.

**WSD separates the axes.** With a warmup–stable–decay schedule, the stable phase holds the
learning rate constant, so two deficits placed at different steps inside it strike at the
**same learning rate and different training times**. At a base budget of 1,350 with 108 warmup
steps, the stable phase runs from step 108 to step 4,320 — a 40× span of training time at one
learning rate.

That is the only design in this repository's drawer that can tell the two apart.

## 3. Schedule and execution

**Schedule.** Linear warmup over a *fixed absolute* step count `W_up`; constant peak rate
through the stable phase; cosine to exactly zero over the final 20% of each rung's budget.
Each leg still anneals to zero, so the convergence property that made v5's endpoint work is
preserved per rung.

**Execution — one trunk, branched legs.** Per (condition, seed):

1. **Trunk:** warmup + stable rate, deficit applied at its window, run to `0.8 × 4B`. Full
   training state — weights, AdamW moments, data-stream RNG, deficit RNG — checkpointed at
   `0.8 × B`, `0.8 × 2B` and trunk end.
2. **Legs:** from each checkpoint, anneal to zero over `0.2 × T_R`. The leg endpoint is that
   rung's registered measurement.

**Two runs at different budgets share a bit-identical trajectory until the shorter one begins
its decay.** "Same deficit, more recovery" stops being an approximation and becomes a
construction. The recovery-handicap argument that `analysis/handicap.py` had to verify
empirically becomes true by construction instead.

## 4. Cost — and this is the surprise

Measured throughput, 3.93 steps/s, from the v5 records. Nine conditions (six Deficit S
onsets, two Deficit F onsets, baseline), eight seeds, rungs 1,350 / 2,700 / 5,400:

| | steps per (condition, seed) | total | wall clock |
| --- | --- | --- | --- |
| Cosine, separate runs ([v6 draft](v6-onset-sweep-design.md)) | 9,450 | 680,400 | **48.1 h** |
| **WSD, shared trunk + legs** | 6,210 | 447,120 | **31.6 h** |

**The WSD path is 34% cheaper**, because the trunk to `0.8 × 4B` is run once instead of the
three rungs being run end to end three times. I had assumed the reverse when recommending
against v6 in the previous draft; the arithmetic says otherwise and the recommendation moves
with it.

The saving is not free — see §6.

## 5. Endpoint

**Unchanged from v5 where it can be.** `gap(T) = c/T^α` per seed, `α` read against Deficit F's
own measured exponent, margin three times the control's per-seed scatter floored at 0.10.
`decision_rules.py`'s primitives apply unchanged; the verdict function is new for the same
reason as in the cosine draft and needs its own rehearsal gate.

**One inference change is forced.** Legs sharing a trunk are strongly dependent, so a
permutation test that shuffles gaps freely across rungs would be exactness theater. Seeds
remain independent, and inference stays where it already is — one exponent per seed, exact
permutation **across seeds**. This is the structure v5 already uses, so nothing is lost.

**The lag/scar decomposition is not restored.** It needs `b` constant, `b` is not constant,
and WSD does not fix that. The question stays out of scope. What WSD buys is the onset axis,
not the absolute one.

### 5.1 The primary contrast, and a subtlety about onset zero

Onsets inside the stable phase are learning-rate-matched. **Onset 0 is not** — it overlaps
warmup, at every rung identically, but at a rising rate rather than the stable one. It is kept
because "the very start" is the theoretically interesting case and because it is v5's early
arm, but it is **the one onset that does not belong to the matched set**, and it may not be
used in the primary contrast.

Proposed onsets, in absolute steps, all fixed for the whole study:

| onset | phase | learning rate |
| --- | --- | --- |
| `0` | warmup + stable | rising, then peak |
| `W_up` | stable | peak |
| `600` | stable | peak |
| `1,400` | stable | peak |
| `2,600` | stable | peak |
| `3,800` | stable | peak |

**Primary contrast:** the exponent difference between the earliest and latest *stable-phase*
onsets, two-sided, 8 vs 8. Under this design that contrast varies training time by roughly 35×
**at a single learning rate**, which no previous design in this project has done.

The registered descriptive curve is all six onsets, with onset 0 reported separately and
labelled as unmatched.

### 5.2 What each path can conclude

| | cosine sweep | WSD |
| --- | --- | --- |
| Shape of α against onset | yes, confounded with LR | yes, at constant LR |
| Whether the shape is a schedule artefact | **no** | **yes** |
| Comparable to v4/v5 | yes — same schedule, `deficits.py` unchanged | **no** — different schedule |
| Lag versus scar | no | no |
| Mechanism | no | no |

## 6. What the saving costs

The cosine draft needs **no new code**: `deficits.py`, `train.py` and the trainer's schedule
are used exactly as frozen. This one needs a trainer that does not exist:

1. **Exact state serialization** — MLX arrays, optimizer moments, both RNG streams. Disk is
   trivial (~30 MB per checkpoint, three per trunk, 72 trunks ≈ 6.5 GB).
2. **Bit-reproducible branching.** A leg resumed from a checkpoint must reproduce, step for
   step, what an uninterrupted run would have done. **Whether this holds under MLX's
   compilation is an open implementation risk** and must be retired by a branch-and-replay
   test before anything is registered. If it does not hold, the whole design collapses to
   separate runs and the 34% saving with it.
3. **A new schedule implementation**, which is a change to `train.py` — outside the freeze
   corpus, but it means the v5 trainer is no longer the thing being run.

And one scientific cost that is not an implementation detail:

4. **Results are not comparable to v4 or v5.** Both ran cosine-over-the-whole-budget. A WSD
   study is a fresh line whose results cannot be read against the two registered ladders. The
   schedule was always a named scope limit; this design makes it load-bearing, because this
   design exists *because* the schedule matters.

## 7. Side by side

| | **A — cosine onset sweep** | **B — WSD trunk-branch** |
| --- | --- | --- |
| Answers | shape of the onset curve | shape, **and** whether it is about time or rate |
| Compute | 48.1 h | **31.6 h** |
| New code | none | checkpointing, branching, WSD schedule |
| Implementation risk | none | **bit-exact branching may not hold** |
| Continuity with v5 | full | none |
| Deficit definitions | frozen, unchanged | frozen, unchanged |
| Verdict logic | new, needs rehearsal | new, needs rehearsal |
| Failure mode | latest onset may not decay at all | branching not reproducible → design void |
| If it succeeds | a curve, of a confounded function | a curve, of the function you wanted |

**The honest summary:** A is cheap in risk and expensive in compute, and answers a question
whose answer is ambiguous by construction. B is cheap in compute and expensive in risk, and
answers the question you actually have — but only if a piece of infrastructure that has never
been built works the first time.

## 8. Decision: B, and the risk is retired

**Settled by measurement, 2026-08-29.** `tools/branch_replay_check.py`.

The test was originally specified as bit-for-bit equality between a resumed run and an
uninterrupted one. **That criterion was wrong and the control proved it:** two runs of an
identical config in separate processes also fail it, diverging around step 28. MLX is not
run-to-run deterministic here, so bit-exactness is unavailable to a run compared against
itself and demanding it of a branch measures the platform, not the design.

Re-run with a control and the registered endpoint — does branching move the held-out loss more
than merely running twice does?

| horizon | two straight runs | straight vs branched | ratio |
| --- | --- | --- | --- |
| 150 steps | 6.26e-07 | 1.04e-07 | 0.17 |
| 600 steps | 6.71e-08 | 1.12e-07 | 1.67 |
| **4,320 steps** — this design's trunk | **1.49e-08** | **1.86e-08** | **1.25** |

Branching costs 25% more than repetition at the length that matters, and both are **five orders
of magnitude below the baseline seed SD** of 0.00235. Divergence does not compound with
horizon; it shrinks, because the decaying learning rate pulls the trajectories together. Weight
drift grows while the measurement does not follow — the weights wander in a flat basin.

**Build this design.** The cosine sweep in [`v6-onset-sweep-design.md`](v6-onset-sweep-design.md)
remains the fallback if the trainer turns out to be harder than the probe suggests, but it is
no longer the recommendation: it costs 16 more hours to map a function that this design
un-confounds.

Scope of the pass, unchanged from what the tool prints: this machine, this MLX version, this
model, these horizons. A branch-replay check stays a **standing gate** — it must pass at the
registered trunk length before v6 is frozen, not just today.

## 9. Not authorized

No preregistration, no freeze, no runs, and in this case no trainer. Turning this into a
registered design requires, at minimum: the branch-and-replay test passing; the WSD schedule
and checkpointing implemented and tested; a verdict function passing a rehearsal gate against
planted onset curves; `preregistration.md` and `CLAIMS.md` rewritten; a new freeze manifest
and tag; fresh seeds (26–33, since the cosine draft claims 18–25).

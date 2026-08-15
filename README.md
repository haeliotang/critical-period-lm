# critical-period-lm

Vision networks have critical periods: blur an image stream during an early window of CNN
training and final accuracy is permanently reduced, no matter how long you train afterwards
(Achille, Rovere & Soatto, ICLR 2019). Does anything like that happen in language-model
pretraining?

This repository is a preregistered test, at a scale that runs on one Mac.

**Both registered ladders are complete.** The design is frozen at `v5`
(tag `cplm-design-v5-frozen`); `v4` is frozen at `cplm-design-v4-frozen` and its result is
final and reported alongside. See [STATUS.md](STATUS.md).

## What was found

| Registered run | Seeds | α(early) − α(late) | Two-sided p | Verdict |
| --- | --- | --- | --- | --- |
| v4 | 5–9 | +0.438 | 0.0002 | **`INCONCLUSIVE`** |
| v5 | 10–17 | +0.392 | 0.0002 | **`REVERSE_ONSET_EFFECT`** |

Under v5, at four budget rungs and eight seeds:

| Condition | 1,350 | 2,700 | 5,400 | 10,800 | α | vs control | reading |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fixed_early_N4` (control) | +0.2106 | +0.1030 | +0.0434 | +0.0197 | 1.158 | anchor | ANCHOR |
| `shuffle_early_N4` | +0.2091 | +0.1019 | +0.0467 | +0.0190 | 1.155 | −0.003 (p 0.95) | LIKE_CONTROL |
| `shuffle_late_N4` | +0.1097 | +0.0643 | +0.0381 | +0.0224 | 0.763 | −0.395 (p 0.0002) | SLOWER_THAN_CONTROL |

Read the first and last columns together. Early damage starts almost twice as large as late
damage and ends smaller: over an 8× budget increase the early gap shrinks 11.0-fold, the
control's 10.7-fold, and the late gap only 4.9-fold. **The two cross.**

So: damage from a deficit applied at mid-training is repaired more slowly than damage from
the same deficit applied at the start, while the early deficit is repaired at the
information-preserving control's rate to three decimal places. **Onset matters, in the
direction opposite to every critical-period account.**

The v4 run measured the same effect (+0.438) and returned `INCONCLUSIVE`, because its margin
— three times the control's own seed scatter — came out at 0.501. That result is not
superseded by v5; it is reported with it.

## What is being measured

Gaps are paired against a seed-matched clean baseline and fitted as `gap(T) = c / T^α` per
seed, with `α` — how fast damage is repaired as the budget grows — the registered quantity.

**Every reading is taken against the negative control, never against a theoretical value.**
`α` mixes the deficit's cost with the baseline curve's own shape, and that shape is common to
every condition at a rung, so it cancels in a comparison and cancels nowhere else.

| | |
| --- | --- |
| Deficit S | shuffle token order within 16-token windows, resampled every time |
| Deficit F (control) | the same operation with one **fixed**, invertible permutation |
| Primary contrast | `α(early) − α(late)`, exact permutation test, 8 vs 8 |
| Margin | 3 × the control's per-seed exponent scatter, floored at 0.10 |
| Ladder | 1,350 / 2,700 / 5,400 / 10,800 steps, 8 seeds, 4 conditions |

Deficit F differs from Deficit S in exactly one respect — its permutation is fixed, so the
reordering is invertible and nothing is destroyed. That single difference is what a negative
control has to be.

## What this does not claim

**Whether the damage is permanent or merely slow to repair is out of scope.** Answering that
needs the deficit's cost in effective training steps held constant across rungs, and four
rungs cannot pin that down. The question is dropped, not answered, and no exponent here may
be pressed into service for it.

Also excluded: anything about larger models, production pretraining, other deficits, other
learning-rate schedules, or human development. **No mechanism is identified and none is
claimed** — the one registered representational measure was never produced, and
[that is recorded](deviations/2026-08-13-cka-registered-but-not-produced.md).

The `REVERSE_ONSET_EFFECT` verdict category was added to the claim register *after*
exploratory data pointed at the pattern. `CLAIMS.md` C4 records the ordering so a reader can
discount it.

## What this is not about

The idea came from a conversation about development and plasticity — whether a model whose
weights are frozen can be said to have grown up. That framing may motivate the work. It
licenses nothing. `CLAIMS.md` forbids any developmental, cognitive or welfare reading of
these numbers, and that prohibition was written on day one, before any data existed.

## Layout

```
preregistration.md   registered design, frozen; v4 and v5 differ only in the instrument
CLAIMS.md            the strongest claims a result may support
STATUS.md            mutable pointer to where the study actually is
deviations/          append-only; every departure, and why, and when it was decided
drafts/              designs considered and not adopted, with the reasons
src/critical_period_lm/
  decision_rules.py  FROZEN judgment logic — byte-identical between v4 and v5
  deficits.py        FROZEN definitions of Deficit S and Deficit F, and the geometry
  freeze.py          hashes the design corpus, detects post-freeze drift
  data.py            TinyStories download, BPE tokenizer, token arrays, digests
  model.py           7.34M-parameter decoder-only transformer in MLX
  train.py           one run; refuses to start without an intact freeze
analysis/report.py   reads every record, no filtering, no discretion
runs/v4/ runs/v5/    registered records, 60 and 128
results/registered/  the reports the frozen code produced
calibration/         exploratory: three pilots and two ladders, excluded from every claim
```

## Running the checks

```bash
make check
```

Compiles, runs 93 tests including the rehearsal gate, verifies the freeze, and refuses to
pass if registered records exist without one.

The rehearsal gate is the part worth knowing about: before the decision code was allowed to
see a real run, it had to return each of its five verdicts correctly against fabricated
ladders with planted decay exponents. A judgment rule that has never been run against a known
answer is not a registered rule.

## How the design got here

Four endpoints were tried and three failed, each recorded in `deviations/`. Each of the first
three smuggled in a parameter from outside the experiment: where the run happened to stop, an
arbitrary 0.01-nat floor, and a theoretical `α = 1` that assumed a constant learning-curve
slope the same data showed falling 30% per doubling. A control-anchored comparison smuggles
in nothing — every quantity it uses is measured in the same runs.

The single most useful rule turned out to be this one: **the registered run may not reuse any
seed the calibration used.** Calibration used seeds 0–4, v4 used 5–9, v5 used 10–17. Had v4
reused the calibration seeds it would have returned `REVERSE_ONSET_EFFECT` and the freeze
would have certified a result that a genuine out-of-sample replication does not support.

`decision_rules.py` hashes identically in the v4 and v5 manifests. v5 improved the instrument
— a fourth rung below the others, eight seeds instead of five — and changed no rule.

## Licence

Code under [MIT](LICENSE); the preregistration, the paper, the deviation log and the run
records under [CC BY 4.0](LICENSE-TEXT.md). The split and the attribution string are in
[LICENSE-TEXT.md](LICENSE-TEXT.md).

Neither licence bears on what the numbers may be used to claim. `CLAIMS.md` does, and its
limits hold wherever the data goes.

# critical-period-lm

Does a data deficit applied early in language-model pretraining leave damage that later
clean training cannot repair — and is the damage specific to *when* it happened rather
than to *how much* of it there was?

Critical learning periods are established in vision: Achille, Rovere and Soatto showed
that blurring images during an early window of CNN training permanently reduces final
accuracy no matter how long the network is afterwards trained on clean data, while a
deficit that leaves low-level image statistics intact leaves no permanent trace. This
repository is a preregistered transfer of that protocol to autoregressive language
modeling, at a scale that runs on one Mac.

**Status: pre-calibration, pre-freeze. No training runs exist and none are authorized.**
See [STATUS.md](STATUS.md).

## What is being tested

| | |
| --- | --- |
| Primary contrast | Same deficit, same duration, applied early versus applied at mid-training |
| Deficit S (predicted to scar) | Shuffle token order within 16-token windows |
| Deficit P (negative control) | Relabel every token id through one fixed bijection |
| Primary endpoint | Held-out cross-entropy at the final step, in nats per token |
| Primary test | Exact one-sided permutation test, 4 versus 4 runs, `α = 0.05` |
| Recovery budget | `2.0 ×` the clean budget after the deficit is removed, fixed in advance |

The early-versus-late contrast is the primary one because a deficit applied to the first
`N` steps also consumes `N` steps of budget. Varying only the duration cannot separate
"early damage is special" from "corrupted data is bad" or from "less training happened".
Holding the deficit and its duration fixed and moving only its onset is what makes the
question a question about a critical period.

Deficit P is what makes a positive result interpretable. It burns exactly the same budget
on non-clean data, and the task it defines is isomorphic to the clean task under a
renaming, so if it recovers and Deficit S does not, the difference is the nature of the
corruption rather than the lost compute. If Deficit P scars, the design has failed and no
critical-period claim survives, whatever Deficit S did.

Read [preregistration.md](preregistration.md) for the registered design and
[CLAIMS.md](CLAIMS.md) for the claims a result would and would not license.

## What this is not about

The idea came out of a conversation about development and plasticity — whether a model
whose weights are frozen can be said to have grown up. That framing may motivate the work.
It licenses nothing. This study measures optimization dynamics in a 10M-parameter
transformer, and `CLAIMS.md` forbids any developmental, cognitive, or welfare reading of
the result. A finding here is a finding about training, at one scale, with two deficits.

## Layout

```
preregistration.md   registered design; frozen before the first run
CLAIMS.md            the strongest claims a result may support
STATUS.md            mutable pointer to where the study actually is
src/critical_period_lm/
  decision_rules.py  FROZEN judgment logic: exact permutation tests, verdicts
  deficits.py        FROZEN definitions of Deficit S and Deficit P
  freeze.py          hashes the design corpus, detects post-freeze drift
  data.py            TinyStories download, BPE tokenizer, token arrays, digests
  model.py           small decoder-only transformer in MLX
  train.py           one run of the grid; writes an immutable run record
tests/               includes the rehearsal gate for the decision rules
runs/                append-only run records; empty until the design is frozen
analysis/            reads runs/, never writes to it
results/             reported outputs
deviations/          append-only log of every departure from the registered design
```

## Freeze rules

The design-defining files are hashed into `freeze-manifest.json` and carried by an
annotated git tag before the first registered run. After that:

- frozen files are never edited; a correction is a new file under `deviations/`;
- `runs/` is append-only, and analysis code reads it without writing to it;
- verdicts come from the frozen code, not from prose;
- a change to the primary endpoint, the direction, the margin, the recovery multiplier, or
  the decision rules invalidates the freeze and needs a new design version and tag.

`decision_rules.py` had to pass its rehearsal before being frozen: on fabricated records it
returns `CRITICAL_PERIOD` under a planted effect, `NO_CRITICAL_PERIOD` under a planted null
it had the resolution to see, `INCONCLUSIVE` under a planted null it did not, and
`DESIGN_FAILURE` when the negative control is planted to scar. A judgment rule that has
never been run against a known answer is not a registered rule.

## Running it

```bash
make check
```

Compiles the package, runs all tests including the rehearsal gate, verifies the freeze if
one exists, and refuses to pass if run artifacts appear before the design is frozen.

```bash
make data
```

Downloads TinyStories, fits a 4096-token byte-level BPE on the training text only, encodes
both splits, and writes `data/manifest.json`. Those digests are folded into every run's
config hash, so a run record is bound to the corpus it was trained on.

```bash
make calibrate
```

An exploratory run, written to `calibration/` rather than `runs/` and exempt from the
freeze gate. This is how the clean budget `T` and the throughput estimate get measured
rather than guessed. Nothing measured here may change the endpoint, the margin, the
direction, or the recovery multiplier.

Two gates in the trainer refuse rather than warn: a registered run will not start unless
the design is frozen and the freeze verifies, and no run will overwrite an existing record,
because a repeat of an identical config is a collision to explain rather than a file to
replace.

## Statistical note

Cells hold 3 to 5 runs, so normal-theory tests are not defensible. Every comparison is an
exact permutation test over the full set of label assignments. With 4 versus 4 the smallest
attainable p-value is `1/70 ≈ 0.014`; with 3 versus 3 it is exactly `0.05`, which is why the
two primary cells carry four seeds and the others do not.

Every non-detection is reported with its minimum detectable effect, and any cell whose
resolution is worse than the registered margin is labeled a **calibrated null
(underpowered)** rather than presented as a clean negative.

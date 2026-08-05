# Study status

**Updated:** 2026-08-06
**Design version:** `v1-draft`
**Lifecycle state:** `DESIGN-DRAFT; PRE-CALIBRATION; PRE-FREEZE`
**Authorized next action:** implement the trainer and the data pipeline, then run the
Section 8.1 calibration to fix the architecture, the clean budget `T`, and the grid
wall-clock estimate. No registered training run is authorized.

The registered design, the claim register, the two deficits, and the decision rules exist
and are under test. `make check` passes: 46 tests, including the Section 7.2 rehearsal gate,
in which the frozen decision code returns each of its four verdicts against a planted
ground truth.

Nothing is frozen yet. `freeze-manifest.json` does not exist, so `make freeze-check`
reports "not frozen" and `make runs-check` refuses to pass if anything appears in `runs/`.

`runs/` is empty. `results/` is empty. No model has been trained, no corpus has been
downloaded, and no number in this repository came from an experiment.

## What still has to exist before the freeze

- A tokenizer and a data pipeline over TinyStories, with the validation split separated and
  hashed before any training begins.
- A trainer that takes a `DeficitSchedule`, honours it per step, and emits an immutable run
  record with config hash, seed, condition, loss curves, and total step count.
- Calibration on the target hardware: measured throughput, the clean budget `T` at which
  baseline validation loss plateaus, and the resulting full-grid wall-clock estimate.
- A budget decision under Section 7.4 if the calibrated grid does not fit the ceiling.
- Verified bibliographic identifiers for the four references in Section 2.

Calibration output feeds the frozen constants. Calibration runs are exploratory, are
excluded from every analysis, and live outside `runs/`.

## Known open design questions

These are recorded because they affect interpretation and are not yet settled. Settling
them before the freeze is an edit to the design; settling them after is an amendment.

- Deficit P may recover so quickly that it is a weak control — it rules out the
  compute-loss explanation regardless, but a near-instant recovery says less about the
  statistics-preserving comparison than a slower one would.
- The mid-training onset for the late arm is fixed at `0.5T` by fiat. A different onset is
  a different experiment, and the choice is not currently justified by anything but
  symmetry.
- Whether a window shuffle at the BPE-token level disturbs sub-word structure enough to be
  a lower-level deficit than intended.

This file is a mutable operational pointer. It is not part of the freeze corpus. The
design-defining decisions are carried by `preregistration.md`, `CLAIMS.md`, the deficit
definitions, and the decision rules.

# Runs

Append-only. One immutable record per completed training run, written by the trainer and
never edited by analysis.

Directories are named by config hash rather than timestamp, so re-running an identical
configuration collides visibly instead of quietly producing a second copy.

Nothing may appear here before the design is frozen. `make runs-check` enforces that.

Each record carries: config hash, seed, condition, deficit schedule, full training and
validation loss curves, final held-out loss, total optimizer steps, environment, and
wall-clock. `total_steps` must be identical across every run in the grid; the decision code
checks this mechanically rather than trusting that it was true.

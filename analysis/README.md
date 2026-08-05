# Analysis

Reads `runs/`. Never writes to it.

Verdicts come from `src/critical_period_lm/decision_rules.py`, which is frozen. Analysis
code here may aggregate, plot, and tabulate; it may not implement a second opinion about
what counts as a scar.

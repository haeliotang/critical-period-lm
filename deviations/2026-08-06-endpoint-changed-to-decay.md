# Primary endpoint changed from a single-budget level to a decay across budgets

**Date:** 2026-08-06
**Design version:** v1.3-draft to v2-draft
**Decided:** after seeing the pilot 3 budget-doubling diagnostic, and because of it
**Pre-freeze:** yes. Nothing was frozen; no registered run exists.

## What changed

The endpoint was the held-out loss difference between a deficit condition and the baseline
at the end of one training budget. It is now the slope of that difference against log
budget, measured across a ladder of budgets, with per-condition verdicts `TRANSIENT`,
`PERSISTENT`, `DECAYING_UNRESOLVED` and `NO_EFFECT`.

## Why

The Section 8.2 diagnostic, on its first use, measured the late-arm gap at two budgets:

| `T_total` | gap to baseline |
| --- | --- |
| 5,400 | +0.0370 |
| 10,800 | +0.0213 |

A 42% fall on one doubling. A difference that shrinks when you train longer is unrepaired
damage, not permanent damage, so the old endpoint was scoring where a run happened to stop.

The problem was made invisible by an earlier fix. Annealing the learning rate to zero was
adopted in v1.2 so that runs would converge; it does that by forcing every condition to stop
moving at the end of its budget, including one that had not finished recovering. Under that
schedule a single-budget endpoint will always report "permanent", because everything is
frozen at the end by construction.

This also explains the three consecutive `DESIGN_FAILURE` verdicts, in which every condition
including two different negative controls scored as scarred. At those budgets nothing had
finished recovering, so no control could recover, and no choice of control would have helped.

## Consequences for the registered design

- Budget is now a treatment variable. The v1.3 mechanical gate requiring identical
  `T_total` across all runs would have failed every valid ladder and has been removed.
- The decay test permutes budget labels rather than flipping paired signs. A paired
  sign-flip test at three seeds enumerates eight assignments, so its smallest attainable
  p-value is 0.125 and it could never reject at 0.05.
- "The control recovers" is now a checkable statement rather than an aspiration: it means
  the control's gap decays to below the margin, which is what the ladder measures.
- `PERSISTENT` is bounded by the top rung and is reported with it. The design cannot say
  "permanent"; it can say "survived a budget of N".
- The duration sweep is deferred, because a ladder multiplies run count by the number of
  rungs and the sweep is descriptive rather than load-bearing.

## Status

The rehearsal gate was rerun against the new rules: on fabricated ladders with planted
shapes, the frozen code returns `CRITICAL_PERIOD` for a flat early gap against a decaying
late one, `NO_CRITICAL_PERIOD` when everything decays away, `DESIGN_FAILURE` when the
control's gap stays put, and `INCONCLUSIVE` when the top rung is too noisy to resolve.

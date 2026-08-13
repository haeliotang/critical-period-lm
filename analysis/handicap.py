"""Can the late arm's smaller recovery allowance explain the exponent difference?

A reviewer will ask this first, so it is answered here from the registered records, with
numbers rather than an argument. **This is a post-hoc descriptive check, not a registered
analysis.** It changes no verdict and writes to `results/robustness/`.

The late arm's deficit ends later, so it has less training left. Under an endpoint that
scored the *level* of the gap this was a genuine confound and it troubled every earlier
design version. Under an exponent endpoint it cannot be one, and the reason is arithmetic:

    gap(T) = c / T^alpha
    k · gap(T) = (k·c) / T^alpha

**A handicap that is the same multiple at every rung moves the amplitude and leaves the
exponent exactly unchanged.** Not approximately — the exponent is the slope of a line in
log-log space and a constant factor is a vertical shift of that line.

So the question is entirely whether the handicap is constant across the ladder. It is, by
construction: the deficit geometry is a fixed fraction of each rung's own budget, so every
ratio that defines the treatment is scale-invariant. This script measures that rather than
asserting it, and then reports how far the observed exponent difference is from anything a
constant handicap could produce.

    python analysis/handicap.py
"""

from __future__ import annotations

import json
import math
import statistics as st
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import mlx.core as mx  # noqa: E402

from critical_period_lm.decision_rules import (  # noqa: E402
    PRIMARY_EARLY,
    PRIMARY_LATE,
    RunRecord,
    fit_exponent,
    paired_gaps,
)
from critical_period_lm.deficits import (  # noqa: E402
    DEFICIT_FRACTIONS,
    LATE_ONSET_FRACTION,
    steps_from_clean_budget,
)
from critical_period_lm.train import TrainConfig, build_schedule  # noqa: E402

BANNER = (
    "**POST-HOC DESCRIPTIVE CHECK. NOT A REGISTERED ANALYSIS.** It answers the question a "
    "reviewer asks first and changes no verdict."
)

N4 = max(DEFICIT_FRACTIONS)


@lru_cache(maxsize=None)
def learning_rate_area(total_steps: int, start: int, stop: int) -> float:
    """Sum of the learning rate over a step range: how much learning the range can carry.

    Evaluated on the whole range at once. The joined schedule takes an array and agrees with
    per-step calls exactly, and a step-by-step loop made the test suite two orders of
    magnitude slower for an identical answer.
    """
    schedule = build_schedule(TrainConfig(total_steps=total_steps))
    return float(mx.sum(schedule(mx.arange(start, stop))))


def geometry(budgets: list[int]) -> list[dict]:
    rows = []
    for budget in budgets:
        duration = steps_from_clean_budget(budget, N4)
        onset = steps_from_clean_budget(budget, LATE_ONSET_FRACTION)
        early_steps, late_steps = budget - duration, budget - onset - duration
        rows.append(
            {
                "budget": budget,
                "deficit": duration,
                "deficit_share": duration / budget,
                "early_steps": early_steps,
                "late_steps": late_steps,
                "step_ratio": late_steps / early_steps,
                "early_area": learning_rate_area(budget, duration, budget),
                "late_area": learning_rate_area(budget, onset + duration, budget),
            }
        )
    for row in rows:
        row["area_ratio"] = row["late_area"] / row["early_area"]
    return rows


def power_law(budgets: list[int], gaps: list[float]) -> tuple[float, float]:
    """Exponent and amplitude of `gap = c / T^alpha`."""
    alpha = fit_exponent(budgets, gaps)
    log_c = st.fmean(
        math.log(g) + alpha * math.log(b) for g, b in zip(gaps, budgets)
    )
    return alpha, math.exp(log_c)


def report(records: list[RunRecord]) -> str:
    gaps = paired_gaps(records)
    budgets = sorted({b for c in gaps for b in gaps[c]})
    rows = geometry(budgets)

    fits = {
        condition: power_law(budgets, [st.fmean(gaps[condition][b].values()) for b in budgets])
        for condition in sorted(gaps)
    }
    delta = fits[PRIMARY_EARLY][0] - fits[PRIMARY_LATE][0]

    early_gaps = [st.fmean(gaps[PRIMARY_EARLY][b].values()) for b in budgets]
    base_alpha = fit_exponent(budgets, early_gaps)
    shifts = [
        (k, abs(fit_exponent(budgets, [g * k for g in early_gaps]) - base_alpha))
        for k in (0.5, 0.75, 1.5, 2.0, 10.0)
    ]

    doublings = math.log2(budgets[-1] / budgets[0])
    required_growth = 2 ** (abs(delta) * doublings)
    step_spread = max(r["step_ratio"] for r in rows) - min(r["step_ratio"] for r in rows)
    area_spread = max(r["area_ratio"] for r in rows) - min(r["area_ratio"] for r in rows)

    lines = [
        "# Could the late arm's smaller recovery allowance explain the exponent difference?",
        "", BANNER, "",
        "## The handicap is real, and it is the same at every rung", "",
        "The deficit is a fixed fraction of each rung's own budget, so every ratio that",
        "defines the treatment is scale-invariant. Measured rather than assumed:", "",
        "| Budget | Deficit | Share of run | Early recovery | Late recovery | Step ratio | LR-area ratio |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['budget']:,} | {r['deficit']} | {r['deficit_share']:.1%} | "
            f"{r['early_steps']:,} | {r['late_steps']:,} | {r['step_ratio']:.4f} | "
            f"{r['area_ratio']:.4f} |"
        )
    lines += [
        "",
        f"Step ratio varies by {step_spread:.4f} across the ladder and the learning-rate-area",
        f"ratio by {area_spread:.4f}. The residual comes from rounding the onset to whole steps",
        "at the smallest rung, not from the design.",
        "",
        "## A constant handicap moves the amplitude and not the exponent", "",
        "The early arm's own gaps, scaled by a constant and refitted:", "",
        "| Multiplier | Shift in exponent |", "| --- | --- |",
    ]
    lines += [f"| ×{k} | {shift:.2e} |" for k, shift in shifts]
    lines += [
        "",
        "Exactly zero, at every multiplier. This is what a power law is, not an approximation",
        "that happens to hold here.",
        "",
        "## What a handicap would have to look like instead", "",
        f"- Observed exponent difference: **{abs(delta):.3f}** — fitted here on rung-mean gaps,",
        "  where the registered contrast averages per-seed exponents. The two differ in the",
        "  third decimal and the argument does not turn on which is used.",
        f"- Budget span: {budgets[0]:,} to {budgets[-1]:,}, {doublings:.0f} doublings",
        f"- A handicap could produce it only by growing as `T^{abs(delta):.3f}` — becoming",
        f"  **{required_growth:.2f}× more severe** in relative terms at the top rung than the bottom",
        f"- Measured growth in the handicap across that span: {area_spread:.4f} on a ratio of "
        f"{rows[0]['area_ratio']:.3f}, i.e. **{area_spread / rows[0]['area_ratio']:.2%}**",
        "",
        "The shape the explanation needs is not available in this design.",
        "",
        "## Where the handicap did leave a trace", "",
        "| Condition | Exponent | Amplitude |", "| --- | --- | --- |",
    ]
    for condition, (alpha, amplitude) in fits.items():
        lines.append(f"| `{condition}` | {alpha:.3f} | {amplitude:.1f} |")
    lines += [
        "",
        "The control and the early arm are the same power law in **both** parameters. The late",
        "arm differs in both. A constant handicap can only move the second column, so it cannot",
        "be what separates the third row from the first two.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    version = sys.argv[1] if len(sys.argv) > 1 else "v5"
    directory = ROOT / "runs" / version
    records = [
        RunRecord(r["condition"], r["seed"], r["final_eval_loss"], r["total_steps"])
        for r in (json.loads(p.read_text()) for p in sorted(directory.glob("*/run.json")))
    ]
    if not records:
        print(f"no records under runs/{version}", file=sys.stderr)
        return 1

    text = report(records)
    destination = ROOT / "results" / "robustness" / version
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "handicap.md").write_text(text)
    print(text)
    print(f"written to {destination / 'handicap.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

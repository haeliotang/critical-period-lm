"""Produce the study verdict from the run records. One pass, no discretion.

This is a driver, not a judge. It reads every run record it finds, hands them to the frozen
decision rules, and formats what comes back. It deliberately has no filtering, no exclusion
rule, and no options that change a verdict — the only way to alter the outcome is to change
which runs exist, which is visible in `runs/`.

A registered report refuses to run unless the freeze is intact, because a verdict produced
by rules that could have been edited after the results appeared is not evidence.

    python analysis/report.py                # registered: reads runs/, writes results/
    python analysis/report.py --calibration  # exploratory: reads calibration/, no freeze

Exploratory output is stamped as such in every artifact it writes. A pilot is not a result.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from critical_period_lm import freeze  # noqa: E402
from critical_period_lm.decision_rules import (  # noqa: E402
    RunRecord,
    paired_gaps,
    study_verdict,
)

RUNS_DIR = ROOT / "runs"
CALIBRATION_DIR = ROOT / "calibration"
RESULTS_DIR = ROOT / "results"

EXPLORATORY_BANNER = (
    "**EXPLORATORY. NOT A REGISTERED RESULT.** These runs are calibration. They are "
    "excluded from the registered analysis, they cannot support any claim in `CLAIMS.md`, "
    "and the design was not frozen when they were produced."
)


def load_runs(directory: Path) -> tuple[list[RunRecord], list[dict]]:
    """Every `run.json` under `directory`. No selection, no exclusion, no ordering effect."""
    raw = [json.loads(path.read_text()) for path in sorted(directory.glob("*/run.json"))]
    records = [
        RunRecord(
            condition=item["condition"],
            seed=item["seed"],
            final_eval_loss=item["final_eval_loss"],
            total_steps=item["total_steps"],
        )
        for item in raw
    ]
    return records, raw


def format_report(result, records: list[RunRecord], raw: list[dict], exploratory: bool) -> str:
    lines = ["# Study report", ""]
    if exploratory:
        lines += [EXPLORATORY_BANNER, ""]

    lines += [f"**Verdict:** `{result.verdict}`", "", "## Basis", ""]
    lines += [f"- {reason}" for reason in result.reasons] or ["- no reasons recorded"]

    if math.isnan(result.level_margin):
        lines += ["", "The ladder did not reach the point where a margin could be computed."]
        return "\n".join(lines) + "\n"

    lines += [
        "",
        "## How the damage decays",
        "",
        "Gap to baseline, paired by seed, fitted as `gap(T) = c / T^alpha`. The exponent is",
        "the answer: **1 means the gap falls exactly as fast as the lost training explains**",
        "(repairable damage, nothing left over), **0 means it does not move at all**, and",
        "anything between means something outlasts the training it cost. Each seed is fitted",
        "separately and the interval is across seeds.",
        "",
        "| Condition | " + " | ".join(f"{b:,}" for b in result.fits[0].budgets)
        + " | alpha | 95% interval | reading |",
        "| --- |" + " --- |" * (len(result.fits[0].budgets) + 3),
    ]
    for fit in result.fits:
        gaps = " | ".join(f"{g:+.4f}" for g in fit.mean_gaps)
        if math.isnan(fit.alpha):
            lines.append(f"| `{fit.condition}` | {gaps} | — | — | {fit.reading} |")
        else:
            lines.append(
                f"| `{fit.condition}` | {gaps} | {fit.alpha:.3f} | "
                f"[{fit.alpha_low:.3f}, {fit.alpha_high:.3f}] | {fit.label} |"
            )

    lines += ["", "### Budget at which each gap reaches the level floor", ""]
    for fit in result.fits:
        if math.isfinite(fit.crossing_budget):
            lines.append(
                f"- `{fit.condition}`: about {fit.crossing_budget:,.0f} steps "
                f"(extrapolated from the fitted power law)"
            )
        else:
            lines.append(f"- `{fit.condition}`: never, on the fitted law")

    lines += [
        "",
        "## Instrument",
        "",
        f"- Top budget: {result.top_budget:,} steps",
        f"- Baseline seed SD at the top budget: {result.baseline_sd:.4f}",
        f"- Level floor (is there damage to model): {result.level_margin:.4f} nats",
        f"- Exponent margin (from the control's own seed spread): "
        f"{result.exponent_margin:.3f}",
        "",
        "## Primary contrast: does onset change the decay rate?",
        "",
        "A critical period predicts early damage is the harder to repair, so it should decay",
        "*more slowly*: `alpha_early < alpha_late`. The one-sided test is that prediction.",
        "The two-sided test exists so that an onset effect running the other way is reported",
        "rather than absorbed into a null.",
        "",
        f"- alpha(early) − alpha(late): {result.primary_delta:+.3f}",
        f"- One-sided p, critical-period direction: {result.primary_p_one_sided:.4f}",
        f"- Two-sided p, onset matters either way: {result.primary_p_two_sided:.4f}",
        "",
        "## Per-seed exponents",
        "",
        "| Condition | seeds fitted | seeds dropped | per-seed alpha |",
        "| --- | --- | --- | --- |",
    ]
    for fit in result.fits:
        per = ", ".join(f"{a:.3f}" for a in fit.per_seed_alpha) or "—"
        lines.append(
            f"| `{fit.condition}` | {fit.seeds_fitted} | {fit.seeds_dropped} | {per} |"
        )

    # Section 5.1 requires dropped runs to be reported. A deficit run with no baseline
    # partner at its own budget and seed contributes no gap, and saying so is the only way
    # a reader can tell an unpairable seed plan from a complete one.
    paired = {
        (condition, budget, seed)
        for condition, by_budget in paired_gaps(records).items()
        for budget, by_seed in by_budget.items()
        for seed in by_seed
    }
    dropped = sorted(
        (r.condition, r.total_steps, r.seed)
        for r in records
        if r.condition != "baseline" and (r.condition, r.total_steps, r.seed) not in paired
    )
    lines += ["", "## Runs dropped for want of a baseline partner", ""]
    if dropped:
        lines.append(
            f"**{len(dropped)} deficit run(s) contributed no gap.** Each was trained and "
            "then could not be paired, so its cost bought nothing. This is a seed-plan "
            "defect, not a data-quality exclusion."
        )
        lines += ["", "| Condition | Budget | Seed |", "| --- | --- | --- |"]
        lines += [f"| `{c}` | {b:,} | {s} |" for c, b, s in dropped]
    else:
        lines.append("None. Every deficit run had a baseline partner at its budget and seed.")

    lines += [
        "",
        "## Runs included",
        "",
        "Every run record found was included. There is no exclusion rule.",
        "",
        "| Condition | Budget | Seed | Final eval loss |",
        "| --- | --- | --- | --- |",
    ]
    for item in sorted(raw, key=lambda r: (r["condition"], r["total_steps"], r["seed"])):
        lines.append(
            f"| `{item['condition']}` | {item['total_steps']:,} | {item['seed']} | "
            f"{item['final_eval_loss']:.4f} |"
        )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--calibration",
        action="store_true",
        help="analyse calibration/ instead of runs/; output is stamped exploratory",
    )
    args = parser.parse_args()

    # Exploratory output stays inside calibration/, which is untracked. Nothing that is
    # not a registered result is ever written into results/.
    source = destination = CALIBRATION_DIR if args.calibration else RUNS_DIR
    if not args.calibration:
        destination = RESULTS_DIR / "registered"

    if not args.calibration:
        problems = freeze.verify_manifest()
        if problems:
            print(
                "a registered report requires an intact freeze; "
                + "; ".join(problems)
                + ". Use --calibration to analyse exploratory runs.",
                file=sys.stderr,
            )
            return 1

    records, raw = load_runs(source)
    if not records:
        print(f"no run records under {source}", file=sys.stderr)
        return 1

    result = study_verdict(records)
    report = format_report(result, records, raw, exploratory=args.calibration)

    destination.mkdir(parents=True, exist_ok=True)
    (destination / "report.md").write_text(report)
    payload = asdict(result)
    payload["exploratory"] = args.calibration
    (destination / "report.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

    print(report)
    print(f"written to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

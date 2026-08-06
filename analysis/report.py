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
from critical_period_lm.decision_rules import RunRecord, study_verdict  # noqa: E402

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


def random_baseline_loss(raw: list[dict]) -> float | None:
    """Loss of a uniform predictor: the top of the range the model had to traverse."""
    vocab_sizes = {item["data_manifest"].get("vocab_size") for item in raw}
    if len(vocab_sizes) != 1 or None in vocab_sizes:
        return None
    return math.log(vocab_sizes.pop())


def format_report(result, records: list[RunRecord], raw: list[dict], exploratory: bool) -> str:
    lines = ["# Study report", ""]
    if exploratory:
        lines += [EXPLORATORY_BANNER, ""]

    lines += [
        f"**Verdict:** `{result.verdict}`",
        "",
        "## Basis",
        "",
    ]
    lines += [f"- {reason}" for reason in result.reasons] or ["- no reasons recorded"]

    if math.isnan(result.margin):
        lines += ["", "The grid did not reach the point where a margin could be computed."]
        return "\n".join(lines) + "\n"

    lines += [
        "",
        "## Instrument",
        "",
        f"- Baseline mean: {result.baseline_mean:.4f} nats/token "
        f"across {sum(r.condition == 'baseline' for r in records)} seeds",
        f"- Baseline seed SD: {result.baseline_sd:.4f}",
        f"- Registered margin: {result.margin:.4f} "
        f"(max of 3 x SD and the 0.01 floor)",
        "",
        "## Primary contrast",
        "",
        f"- Delta (early minus late): {result.primary_delta:+.4f} nats/token",
        f"- Exact permutation p: {result.primary_p_value:.4f}",
        f"- Minimum detectable effect: {result.primary_mde:.4f}",
        "",
        "## Cells",
        "",
        "| Condition | n | Delta vs baseline | p | MDE | Verdict |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for cell in result.cells:
        mde = "unbounded" if math.isinf(cell.mde) else f"{cell.mde:.4f}"
        lines.append(
            f"| `{cell.condition}` | {cell.n} | {cell.delta:+.4f} | "
            f"{cell.p_value:.4f} | {mde} | {cell.label} |"
        )

    lines += [
        "",
        "## Runs included",
        "",
        "Every run record found was included. There is no exclusion rule.",
        "",
        "| Condition | Seed | Final eval loss | Total steps |",
        "| --- | --- | --- | --- |",
    ]
    for item in sorted(raw, key=lambda r: (r["condition"], r["seed"])):
        lines.append(
            f"| `{item['condition']}` | {item['seed']} | "
            f"{item['final_eval_loss']:.4f} | {item['total_steps']} |"
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

    result = study_verdict(records, random_baseline_loss(raw))
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

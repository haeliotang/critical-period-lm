"""Specification multiverse: how much of each registered verdict was the analysis choice?

**This is not a result and can never become one.** The registered verdicts are whatever
`decision_rules.py` returned — v4 `INCONCLUSIVE`, v5 `REVERSE_ONSET_EFFECT` — and this module
cannot change them. It was written after both were known, which is the only honest place to
put a robustness exhibit but also the reason it is labelled as one in every artifact it
produces.

What it does is enumerate the analyses a reasonable person might have preregistered instead,
run each one over the same untouched records, and report how the verdict moves. The frozen
specification is one cell of that grid and is marked in every table.

## The excluded half matters more than the included half

Del Giudice & Gangestad's warning about multiverse analysis is that including options already
known to be wrong lets bad pipelines vote, and a spread manufactured that way says nothing.
Four are therefore excluded by name, with reasons, rather than swept in to inflate the count:

- **Unpaired gaps.** Comparing condition means to baseline means without matching seeds
  discards a variance component the design registered for a stated reason. Strictly worse,
  not merely different.
- **Nudging non-positive gaps into the logarithm.** A gap at or below zero is noise around
  zero, not decay; `fit_exponent` refuses it and the preregistration says so.
- **Reading the exponent against the theoretical value 1.** This is the design v3 defect,
  refuted empirically by its own data: the baseline log-slope falls about 30% per doubling,
  so the pure-lag anchor is not 1 and the corrected value is too fragile to replace it.
  A refuted anchor does not get a vote.
- **Dropping the outlier seed.** Post-hoc exclusion with no preregistered rule. It appears
  in `STATUS.md` as a labelled sensitivity note and must not be laundered into a
  defensible specification here.

## What varies

| Dimension | Levels | Frozen |
| --- | --- | --- |
| Scale the margin is built from | control / pooled-all / pooled-arms / MAD-control | control |
| Multiple of that scale | 2, 3, 4 | 3 |
| Floor under the margin | 0.05, 0.10, 0.20 | 0.10 |
| Exponent estimator | OLS / Theil-Sen | OLS |
| Rungs used | all / drop the lowest | all |

The verdict logic itself does not vary. Only the quantities feeding it do.

    python analysis/multiverse.py v4
    python analysis/multiverse.py v5
"""

from __future__ import annotations

import json
import math
import statistics as st
import sys
from itertools import combinations, product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from critical_period_lm.decision_rules import (  # noqa: E402
    ALPHA,
    CRITICAL_PERIOD,
    INCONCLUSIVE,
    NO_CRITICAL_PERIOD,
    NEGATIVE_CONTROL_PREFIX,
    PRIMARY_EARLY,
    PRIMARY_LATE,
    REVERSE_ONSET_EFFECT,
    RunRecord,
    exact_permutation_p,
    fit_exponent,
    paired_gaps,
)

BANNER = (
    "**ROBUSTNESS EXHIBIT. NOT A RESULT.** The registered verdict is whatever the frozen "
    "decision code returned; it is reported in `results/registered/` and nothing here "
    "revises it. This grid was enumerated after both registered verdicts were known, and "
    "exists to show how much of each one rode on a single analysis choice."
)

EXCLUSIONS = [
    ("unpaired gaps",
     "discards the seed pairing the design registered; strictly worse, not merely different"),
    ("nudging non-positive gaps into the logarithm",
     "a gap at or below zero is noise around zero, not decay; the frozen fitter refuses it"),
    ("anchoring the exponent on the theoretical value 1",
     "the design v3 defect, refuted by its own data: the baseline log-slope falls ~30% per "
     "doubling, so the pure-lag anchor is not 1"),
    ("dropping the outlier seed",
     "post-hoc exclusion with no preregistered rule; it is a labelled sensitivity note in "
     "STATUS.md, not a defensible specification"),
]

SCALES = ("control", "pooled-all", "pooled-arms", "mad-control")
MULTIPLES = (2.0, 3.0, 4.0)
FLOORS = (0.05, 0.10, 0.20)
ESTIMATORS = ("ols", "theil-sen")
RUNGS = ("all", "drop-lowest")

FROZEN = {
    "scale": "control",
    "multiple": 3.0,
    "floor": 0.10,
    "estimator": "ols",
    "rungs": "all",
}


def theil_sen_exponent(budgets: list[int], gaps: list[float]) -> float:
    """Median of pairwise log-log slopes. One bad rung moves it far less than it moves OLS."""
    if any(g <= 0 for g in gaps):
        raise ValueError("exponent fitting requires strictly positive gaps")
    slopes = [
        -(math.log(gaps[j]) - math.log(gaps[i])) / (math.log(budgets[j]) - math.log(budgets[i]))
        for i, j in combinations(range(len(budgets)), 2)
    ]
    return st.median(slopes)


def per_seed_exponents(gaps_by_budget, rungs, estimator) -> list[float]:
    seeds = sorted(set.intersection(*(set(gaps_by_budget[b]) for b in rungs)))
    fit = fit_exponent if estimator == "ols" else theil_sen_exponent
    out = []
    for seed in seeds:
        try:
            out.append(fit(list(rungs), [gaps_by_budget[b][seed] for b in rungs]))
        except ValueError:
            continue
    return out


def margin_from(scale: str, alphas: dict[str, list[float]], multiple: float, floor: float):
    """The exponent margin under one choice of where its scale comes from."""
    control = [a for c, v in alphas.items() if c.startswith(NEGATIVE_CONTROL_PREFIX) for a in v]
    if scale == "control":
        spread = st.stdev(control) if len(control) > 1 else math.nan
    elif scale == "mad-control":
        median = st.median(control)
        spread = 1.4826 * st.median([abs(a - median) for a in control])
    else:
        wanted = (
            (PRIMARY_EARLY, PRIMARY_LATE) if scale == "pooled-arms" else tuple(alphas)
        )
        variances = [st.variance(alphas[c]) for c in wanted if len(alphas.get(c, [])) > 1]
        spread = math.sqrt(sum(variances) / len(variances)) if variances else math.nan
    return max(multiple * spread, floor) if spread == spread else math.nan


def verdict_under(records: list[RunRecord], spec: dict) -> tuple[str, float, float, float]:
    """The frozen verdict logic, fed by one specification's quantities."""
    gaps = paired_gaps(records)
    budgets = sorted({b for c in gaps for b in gaps[c]})
    rungs = tuple(budgets if spec["rungs"] == "all" else budgets[1:])
    if len(rungs) < 2:
        return "UNFITTABLE", math.nan, math.nan, math.nan

    alphas = {c: per_seed_exponents(gaps[c], rungs, spec["estimator"]) for c in gaps}
    if any(len(v) < 2 for v in alphas.values()):
        return "UNFITTABLE", math.nan, math.nan, math.nan

    margin = margin_from(spec["scale"], alphas, spec["multiple"], spec["floor"])
    early, late = alphas[PRIMARY_EARLY], alphas[PRIMARY_LATE]
    delta = st.fmean(early) - st.fmean(late)
    one_sided = exact_permutation_p(late, early)
    two_sided = exact_permutation_p(early, late, two_sided=True)

    if one_sided <= ALPHA and -delta >= margin:
        verdict = CRITICAL_PERIOD
    elif two_sided <= ALPHA and delta >= margin:
        verdict = REVERSE_ONSET_EFFECT
    elif two_sided > ALPHA and abs(delta) < margin:
        verdict = NO_CRITICAL_PERIOD
    else:
        verdict = INCONCLUSIVE
    return verdict, delta, margin, two_sided


def enumerate_specs():
    for scale, multiple, floor, estimator, rungs in product(
        SCALES, MULTIPLES, FLOORS, ESTIMATORS, RUNGS
    ):
        yield {
            "scale": scale, "multiple": multiple, "floor": floor,
            "estimator": estimator, "rungs": rungs,
        }


def load(directory: Path) -> list[RunRecord]:
    return [
        RunRecord(r["condition"], r["seed"], r["final_eval_loss"], r["total_steps"])
        for r in (json.loads(p.read_text()) for p in sorted(directory.glob("*/run.json")))
    ]


def report(version: str, records: list[RunRecord], registered: str) -> str:
    rows = [(spec, *verdict_under(records, spec)) for spec in enumerate_specs()]
    frozen_row = next(r for r in rows if r[0] == FROZEN)

    counts: dict[str, int] = {}
    for _, verdict, *_ in rows:
        counts[verdict] = counts.get(verdict, 0) + 1
    total = len(rows)

    lines = [
        f"# Specification multiverse — {version}", "", BANNER, "",
        f"**Registered verdict:** `{registered}`",
        f"**Frozen specification reproduces it:** "
        f"{'yes' if frozen_row[1] == registered else '**NO — investigate**'} "
        f"(`{frozen_row[1]}`, delta {frozen_row[2]:+.3f}, margin {frozen_row[3]:.3f})",
        "", f"## Verdict across {total} defensible specifications", "",
        "| Verdict | Specifications | Share |", "| --- | --- | --- |",
    ]
    for verdict, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        mark = "  ← frozen" if verdict == frozen_row[1] else ""
        lines.append(f"| `{verdict}`{mark} | {n} | {n / total:.0%} |")

    lines += ["", "## Which choice moves the verdict", "",
              "Share of specifications returning the registered verdict, held at each level.",
              ""]
    for name, levels in (
        ("scale", SCALES), ("multiple", MULTIPLES), ("floor", FLOORS),
        ("estimator", ESTIMATORS), ("rungs", RUNGS),
    ):
        lines += [f"**{name}**", "", "| Level | Agrees with registered | |", "| --- | --- | --- |"]
        for level in levels:
            subset = [r for r in rows if r[0][name] == level]
            agree = sum(1 for r in subset if r[1] == registered) / len(subset)
            frozen_mark = " ← frozen" if FROZEN[name] == level else ""
            lines.append(f"| `{level}`{frozen_mark} | {agree:.0%} | {'█' * round(agree * 20)} |")
        lines.append("")

    lines += ["## Specifications excluded by name, and why", "",
              "Including options already known to be wrong lets bad pipelines vote.", "",
              "| Excluded | Reason |", "| --- | --- |"]
    lines += [f"| {what} | {why} |" for what, why in EXCLUSIONS]

    lines += ["", "## Every cell", "",
              "| scale | mult | floor | estimator | rungs | delta | margin | 2-sided p | verdict |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for spec, verdict, delta, margin, two_sided in rows:
        mark = " **←**" if spec == FROZEN else ""
        lines.append(
            f"| {spec['scale']} | {spec['multiple']:.0f} | {spec['floor']:.2f} | "
            f"{spec['estimator']} | {spec['rungs']} | {delta:+.3f} | {margin:.3f} | "
            f"{two_sided:.5f} | `{verdict}`{mark} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    version = sys.argv[1] if len(sys.argv) > 1 else "v5"
    records = load(ROOT / "runs" / version)
    if not records:
        print(f"no records under runs/{version}", file=sys.stderr)
        return 1
    registered = json.loads(
        (ROOT / "results" / "registered" / version / "report.json").read_text()
    )["verdict"]

    text = report(version, records, registered)
    destination = ROOT / "results" / "robustness" / version
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "multiverse.md").write_text(text)
    print(text.split("## Every cell")[0])
    print(f"full grid written to {destination / 'multiverse.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

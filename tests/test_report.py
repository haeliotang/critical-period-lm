"""Tests for the analysis driver.

The driver must have no discretion: it reads every record, it cannot exclude one, and it
cannot produce a registered verdict without an intact freeze. Those three properties are
what make the report evidence rather than a summary someone assembled.
"""

import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("report", ROOT / "analysis" / "report.py")
report = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(report)

from critical_period_lm import freeze  # noqa: E402
from critical_period_lm.decision_rules import CRITICAL_PERIOD, DESIGN_FAILURE  # noqa: E402

BUDGETS = (2_700, 5_400, 10_800)
TOP = BUDGETS[-1]
BASELINE = {2_700: [2.2844, 2.2962, 2.2893], 5_400: [2.0307, 2.0382, 2.0290],
            10_800: [1.8544, 1.8581, 1.8545]}
LAG_ALPHAS = (1.05, 0.98, 1.02)
SLOW_ALPHAS = (0.55, 0.50, 0.52)


def gaps_for(alphas, top_gap=0.05):
    return {b: [top_gap * (TOP / b) ** a for a in alphas] for b in BUDGETS}


# Early damage decaying more slowly than late damage: a planted critical period.
LADDER = {"shuffle_early_N4": gaps_for(SLOW_ALPHAS), "shuffle_late_N4": gaps_for(LAG_ALPHAS),
          "fixed_early_N4": gaps_for(LAG_ALPHAS)}


def write_ladder(directory: Path, gaps=LADDER, baseline=BASELINE) -> None:
    def emit(condition, budget, seed, loss):
        run = directory / f"{condition}-{budget}-{seed}"
        run.mkdir(parents=True)
        (run / "run.json").write_text(
            json.dumps(
                {
                    "condition": condition,
                    "seed": seed,
                    "final_eval_loss": loss,
                    "total_steps": budget,
                    "data_manifest": {"vocab_size": 4096},
                }
            )
        )

    for budget, losses in baseline.items():
        for seed, loss in enumerate(losses):
            emit("baseline", budget, seed, loss)
    for condition, by_budget in gaps.items():
        for budget, values in by_budget.items():
            for seed, gap in enumerate(values):
                emit(condition, budget, seed, baseline[budget][seed] + gap)


class LoadingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        write_ladder(self.dir)

    def test_every_record_is_loaded(self):
        records, raw = report.load_runs(self.dir)
        expected = len(BASELINE) * 3 + sum(len(b) * 3 for b in LADDER.values())
        self.assertEqual(len(records), expected)
        self.assertEqual(len(raw), len(records))

    def test_the_budget_is_carried_into_the_record(self):
        records, _ = report.load_runs(self.dir)
        self.assertEqual({r.total_steps for r in records}, set(BUDGETS))

    def test_an_extra_run_changes_what_is_analysed(self):
        # The only lever on the outcome is which runs exist, and that is visible on disk.
        before, _ = report.load_runs(self.dir)
        extra = self.dir / "baseline-21600-99"
        extra.mkdir()
        (extra / "run.json").write_text(
            json.dumps(
                {
                    "condition": "baseline",
                    "seed": 99,
                    "final_eval_loss": 1.9,
                    "total_steps": 21_600,
                    "data_manifest": {"vocab_size": 4096},
                }
            )
        )
        after, _ = report.load_runs(self.dir)
        self.assertEqual(len(after), len(before) + 1)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_a_planted_effect_reports_a_critical_period_with_every_run_listed(self):
        write_ladder(self.dir)
        records, raw = report.load_runs(self.dir)
        result = report.study_verdict(records)
        text = report.format_report(result, records, raw, exploratory=False)

        self.assertEqual(result.verdict, CRITICAL_PERIOD)
        self.assertIn("`CRITICAL_PERIOD`", text)
        for condition in LADDER:
            self.assertIn(f"`{condition}`", text)
        self.assertIn("How the damage decays", text)
        self.assertNotIn("EXPLORATORY", text)

    def test_every_budget_rung_appears_in_the_decay_table(self):
        write_ladder(self.dir)
        records, raw = report.load_runs(self.dir)
        text = report.format_report(
            report.study_verdict(records), records, raw, exploratory=False
        )
        for budget in BUDGETS:
            self.assertIn(f"{budget:,}", text)

    def test_exploratory_output_says_so(self):
        write_ladder(self.dir)
        records, raw = report.load_runs(self.dir)
        text = report.format_report(
            report.study_verdict(records), records, raw, exploratory=True
        )
        self.assertIn("NOT A REGISTERED RESULT", text)

    def test_the_exponent_and_its_interval_appear(self):
        write_ladder(self.dir)
        records, raw = report.load_runs(self.dir)
        text = report.format_report(
            report.study_verdict(records), records, raw, exploratory=False
        )
        self.assertIn("alpha", text)
        self.assertIn("Per-seed exponents", text)
        self.assertIn("does onset change the decay rate", text)

    def test_an_incomplete_ladder_formats_without_crashing(self):
        # One rung is a design failure with a NaN margin; the report must still render,
        # because a ladder mid-flight is the normal case for this path.
        write_ladder(self.dir, gaps={}, baseline={2_700: BASELINE[2_700]})
        records, raw = report.load_runs(self.dir)
        result = report.study_verdict(records)
        text = report.format_report(result, records, raw, exploratory=True)
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertIn("Study report", text)


class DroppedRunTests(unittest.TestCase):
    """A run that was trained and could not be paired must be visible in the report."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def _text(self):
        records, raw = report.load_runs(self.dir)
        return report.format_report(
            report.study_verdict(records), records, raw, exploratory=True
        )

    def test_a_complete_ladder_reports_no_drops(self):
        write_ladder(self.dir)
        self.assertIn("None. Every deficit run had a baseline partner", self._text())

    def test_a_deficit_seed_with_no_baseline_partner_is_reported(self):
        # The exact defect ladder 1 hit: primary arms carried a seed the baseline did not,
        # so those runs trained and then contributed nothing.
        write_ladder(self.dir)
        for budget in BUDGETS:
            run = self.dir / f"shuffle_early_N4-{budget}-3"
            run.mkdir()
            (run / "run.json").write_text(
                json.dumps(
                    {
                        "condition": "shuffle_early_N4",
                        "seed": 3,
                        "final_eval_loss": 1.9,
                        "total_steps": budget,
                        "data_manifest": {"vocab_size": 4096},
                    }
                )
            )
        text = self._text()
        self.assertIn("3 deficit run(s) contributed no gap", text)
        self.assertIn("seed-plan defect", text)


class FreezeGateTests(unittest.TestCase):
    def test_a_registered_report_refuses_without_an_intact_freeze(self):
        with patch.object(freeze, "verify_manifest", return_value=["design not frozen"]):
            with patch.object(report.sys, "argv", ["report.py"]):
                self.assertEqual(report.main(), 1)


if __name__ == "__main__":
    unittest.main()

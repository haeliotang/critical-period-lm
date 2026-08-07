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

BUDGETS = (5_400, 10_800, 21_600)
BASELINE = {5_400: [2.0300, 2.0360, 2.0330], 10_800: [1.8540, 1.8600, 1.8570],
            21_600: [1.7000, 1.7060, 1.7030]}
FLAT = {5_400: [0.050, 0.052, 0.048], 10_800: [0.051, 0.049, 0.050],
        21_600: [0.049, 0.051, 0.050]}
DECAYS = {5_400: [0.050, 0.052, 0.048], 10_800: [0.020, 0.021, 0.019],
          21_600: [0.004, 0.005, 0.003]}
LADDER = {"shuffle_early_N4": FLAT, "shuffle_late_N4": DECAYS, "fixed_early_N4": DECAYS}


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
        self.assertIn("Does the damage decay?", text)
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

    def test_an_incomplete_ladder_formats_without_crashing(self):
        # One rung is a design failure with a NaN margin; the report must still render,
        # because a ladder mid-flight is the normal case for this path.
        write_ladder(self.dir, gaps={}, baseline={5_400: BASELINE[5_400]})
        records, raw = report.load_runs(self.dir)
        result = report.study_verdict(records)
        text = report.format_report(result, records, raw, exploratory=True)
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertIn("Study report", text)


class FreezeGateTests(unittest.TestCase):
    def test_a_registered_report_refuses_without_an_intact_freeze(self):
        with patch.object(freeze, "verify_manifest", return_value=["design not frozen"]):
            with patch.object(report.sys, "argv", ["report.py"]):
                self.assertEqual(report.main(), 1)


if __name__ == "__main__":
    unittest.main()

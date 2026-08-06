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

GRID = {
    "baseline": [1.000, 1.004, 0.998, 1.002, 1.001],
    "shuffle_early_N4": [1.200, 1.210, 1.190, 1.205],
    "shuffle_late_N4": [1.050, 1.060, 1.040, 1.055],
    "permute_early_N4": [1.001, 1.003, 0.999],
}


def write_grid(directory: Path, grid=GRID, total_steps=21_600, vocab_size=4096) -> None:
    for condition, losses in grid.items():
        for seed, loss in enumerate(losses):
            run = directory / f"{condition}-{seed}"
            run.mkdir(parents=True)
            (run / "run.json").write_text(
                json.dumps(
                    {
                        "condition": condition,
                        "seed": seed,
                        "final_eval_loss": loss,
                        "total_steps": total_steps,
                        "data_manifest": {"vocab_size": vocab_size},
                    }
                )
            )


class LoadingTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        write_grid(self.dir)

    def test_every_record_is_loaded(self):
        records, raw = report.load_runs(self.dir)
        self.assertEqual(len(records), sum(len(v) for v in GRID.values()))
        self.assertEqual(len(raw), len(records))

    def test_an_extra_run_changes_the_result(self):
        # The only lever on the outcome is which runs exist, and that is visible on disk.
        before, _ = report.load_runs(self.dir)
        extra = self.dir / "baseline-99"
        extra.mkdir()
        (extra / "run.json").write_text(
            json.dumps(
                {
                    "condition": "baseline",
                    "seed": 99,
                    "final_eval_loss": 1.5,
                    "total_steps": 21_600,
                    "data_manifest": {"vocab_size": 4096},
                }
            )
        )
        after, _ = report.load_runs(self.dir)
        self.assertEqual(len(after), len(before) + 1)

    def test_the_random_reference_is_the_log_of_the_vocabulary(self):
        _, raw = report.load_runs(self.dir)
        self.assertAlmostEqual(report.random_baseline_loss(raw), 8.3178, places=3)

    def test_a_mixed_corpus_yields_no_random_reference(self):
        odd = self.dir / "baseline-98"
        odd.mkdir()
        (odd / "run.json").write_text(
            json.dumps(
                {
                    "condition": "baseline",
                    "seed": 98,
                    "final_eval_loss": 1.0,
                    "total_steps": 21_600,
                    "data_manifest": {"vocab_size": 8192},
                }
            )
        )
        _, raw = report.load_runs(self.dir)
        self.assertIsNone(report.random_baseline_loss(raw))


class ReportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_a_planted_effect_reports_a_critical_period_with_every_run_listed(self):
        write_grid(self.dir)
        records, raw = report.load_runs(self.dir)
        result = report.study_verdict(records, report.random_baseline_loss(raw))
        text = report.format_report(result, records, raw, exploratory=False)

        self.assertEqual(result.verdict, CRITICAL_PERIOD)
        self.assertIn("`CRITICAL_PERIOD`", text)
        for condition in GRID:
            self.assertIn(f"`{condition}`", text)
        self.assertNotIn("EXPLORATORY", text)

    def test_exploratory_output_says_so(self):
        write_grid(self.dir)
        records, raw = report.load_runs(self.dir)
        result = report.study_verdict(records, report.random_baseline_loss(raw))
        text = report.format_report(result, records, raw, exploratory=True)
        self.assertIn("NOT A REGISTERED RESULT", text)

    def test_an_incomplete_grid_formats_without_crashing(self):
        # A partial grid gives a design failure and a NaN margin; the report must still
        # render, because a pilot mid-flight is the normal case for this path.
        write_grid(self.dir, grid={"baseline": [1.0, 1.01]})
        records, raw = report.load_runs(self.dir)
        result = report.study_verdict(records, report.random_baseline_loss(raw))
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

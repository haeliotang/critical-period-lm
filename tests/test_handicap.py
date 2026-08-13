"""Tests for the recovery-handicap check.

The check's whole content is one arithmetic claim — a constant multiplicative handicap moves
a power law's amplitude and not its exponent — plus a measurement of whether the design's
handicap is in fact constant. Both are tested here; if either failed, the reviewer answer
would be wrong rather than merely unpersuasive.
"""

import importlib.util
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("handicap", ROOT / "analysis" / "handicap.py")
handicap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(handicap)

from critical_period_lm.decision_rules import RunRecord, fit_exponent  # noqa: E402

BUDGETS = [1_350, 2_700, 5_400, 10_800]


class AmplitudeVersusExponentTests(unittest.TestCase):
    """The claim the whole check rests on."""

    def test_a_constant_multiplier_leaves_the_exponent_exactly_unchanged(self):
        gaps = [0.05 * (10_800 / b) ** 1.15 for b in BUDGETS]
        base = fit_exponent(BUDGETS, gaps)
        for k in (0.01, 0.5, 2.0, 100.0):
            with self.subTest(k=k):
                self.assertEqual(fit_exponent(BUDGETS, [g * k for g in gaps]), base)

    def test_a_constant_multiplier_moves_the_amplitude_by_that_multiplier(self):
        gaps = [0.05 * (10_800 / b) ** 1.15 for b in BUDGETS]
        _, c = handicap.power_law(BUDGETS, gaps)
        _, c3 = handicap.power_law(BUDGETS, [g * 3.0 for g in gaps])
        self.assertAlmostEqual(c3 / c, 3.0, places=9)

    def test_a_budget_dependent_handicap_does_move_the_exponent(self):
        # The alternative explanation is not impossible in principle -- it is unavailable in
        # this design. A handicap growing as T^0.4 shifts the exponent by exactly 0.4.
        gaps = [0.05 * (10_800 / b) ** 1.15 for b in BUDGETS]
        grown = [g * (b / BUDGETS[0]) ** -0.4 for g, b in zip(gaps, BUDGETS)]
        self.assertAlmostEqual(fit_exponent(BUDGETS, grown) - fit_exponent(BUDGETS, gaps), 0.4)

    def test_power_law_round_trips(self):
        for alpha, c in ((0.75, 30.0), (1.15, 900.0)):
            gaps = [c / b**alpha for b in BUDGETS]
            got_alpha, got_c = handicap.power_law(BUDGETS, gaps)
            self.assertAlmostEqual(got_alpha, alpha, places=9)
            self.assertAlmostEqual(got_c, c, places=6)


class GeometryTests(unittest.TestCase):
    """Whether the design's handicap is in fact the same at every rung."""

    def setUp(self):
        self.rows = handicap.geometry(BUDGETS)

    def test_the_deficit_is_the_same_share_of_every_rung(self):
        shares = [r["deficit_share"] for r in self.rows]
        self.assertLess(max(shares) - min(shares), 0.001)

    def test_the_recovery_step_ratio_is_the_same_at_every_rung(self):
        ratios = [r["step_ratio"] for r in self.rows]
        self.assertLess(max(ratios) - min(ratios), 0.01)

    def test_the_learning_rate_area_ratio_is_the_same_at_every_rung(self):
        # Closer to "how much recovery is available" than a step count, and it is the
        # quantity a sceptic would reach for.
        ratios = [r["area_ratio"] for r in self.rows]
        self.assertLess(max(ratios) - min(ratios), 0.01)

    def test_the_late_arm_really_does_have_less_recovery(self):
        # The handicap is real; the point is only that it is constant.
        for row in self.rows:
            self.assertLess(row["late_steps"], row["early_steps"])
            self.assertLess(row["area_ratio"], 1.0)


class ReportTests(unittest.TestCase):
    def _records(self, early_alpha, late_alpha):
        baseline = {b: [2.0 + 0.001 * s for s in range(4)] for b in BUDGETS}
        records = [
            RunRecord("baseline", s, loss, b)
            for b, losses in baseline.items()
            for s, loss in enumerate(losses)
        ]
        for condition, alpha in (
            ("shuffle_early_N4", early_alpha),
            ("shuffle_late_N4", late_alpha),
            ("fixed_early_N4", early_alpha),
        ):
            for b in BUDGETS:
                for s in range(4):
                    gap = 0.05 * (10_800 / b) ** alpha
                    records.append(RunRecord(condition, s, baseline[b][s] + gap, b))
        return records

    def test_the_report_says_it_is_not_a_registered_analysis(self):
        text = handicap.report(self._records(1.15, 0.76))
        self.assertIn("NOT A REGISTERED ANALYSIS", text)
        self.assertIn("changes no verdict", text)

    def test_the_report_states_the_growth_a_handicap_would_need(self):
        text = handicap.report(self._records(1.15, 0.76))
        self.assertIn("more severe", text)
        self.assertIn("not available in this design", text)

    def test_the_report_lists_every_condition_with_both_parameters(self):
        text = handicap.report(self._records(1.15, 0.76))
        for condition in ("fixed_early_N4", "shuffle_early_N4", "shuffle_late_N4"):
            self.assertIn(f"`{condition}`", text)
        self.assertIn("Amplitude", text)


if __name__ == "__main__":
    unittest.main()

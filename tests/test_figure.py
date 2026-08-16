"""Tests for the paper's figure.

A figure is an argument, so the arithmetic under it is tested like any other. The claim the
figure makes that the tables do not is the crossing: that the early and late fits meet at a
budget inside the ladder. If `crossing` were wrong the picture would assert something the
records do not support, and a reader would have no way to tell.
"""

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("figure", ROOT / "analysis" / "figure.py")
figure = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(figure)

from critical_period_lm.decision_rules import BASELINE, RunRecord  # noqa: E402

BUDGETS = [1_350, 2_700, 5_400, 10_800]


class PowerLawTests(unittest.TestCase):
    def test_round_trips_both_parameters(self):
        for alpha, c in ((0.763, 26.8), (1.151, 871.0)):
            gaps = [c / b**alpha for b in BUDGETS]
            got_alpha, got_c = figure.power_law(BUDGETS, gaps)
            self.assertAlmostEqual(got_alpha, alpha, places=9)
            self.assertAlmostEqual(got_c, c, places=6)


class CrossingTests(unittest.TestCase):
    def test_finds_the_budget_where_two_laws_meet(self):
        # Planted: the two curves are equal at exactly 4,000 by construction.
        steep, shallow = (1.2, 0.7)
        c_shallow = 50.0
        c_steep = c_shallow * 4_000 ** (steep - shallow)
        at = figure.crossing((steep, c_steep), (shallow, c_shallow))
        self.assertAlmostEqual(at, 4_000.0, places=6)

    def test_parallel_laws_never_cross(self):
        self.assertIsNone(figure.crossing((1.1, 500.0), (1.1, 20.0)))

    def test_the_crossing_is_where_both_laws_give_the_same_gap(self):
        a, b = (1.151, 871.0), (0.763, 26.8)
        at = figure.crossing(a, b)
        self.assertAlmostEqual(a[1] / at ** a[0], b[1] / at ** b[0], places=12)


class BuildTests(unittest.TestCase):
    def _records(self, early_alpha, late_alpha, seeds=8):
        baseline = {b: [2.0 + 0.001 * s for s in range(seeds)] for b in BUDGETS}
        records = [
            RunRecord(BASELINE, s, loss, b)
            for b, losses in baseline.items()
            for s, loss in enumerate(losses)
        ]
        for condition, alpha in (
            ("shuffle_early_N4", early_alpha),
            ("shuffle_late_N4", late_alpha),
            ("fixed_early_N4", early_alpha),
        ):
            for b in BUDGETS:
                for s in range(seeds):
                    records.append(
                        RunRecord(condition, s, baseline[b][s] + 0.05 * (10_800 / b) ** alpha, b)
                    )
        return records

    def test_the_baseline_is_never_plotted(self):
        self.assertNotIn(BASELINE, figure.ORDER)

    def test_one_exponent_per_seed_per_condition(self):
        _, _, per_seed = figure.build(self._records(1.15, 0.76), margin=0.32)
        for condition in figure.ORDER:
            self.assertEqual(len(per_seed[condition]), 8)

    def test_planted_exponents_are_recovered(self):
        _, fits, _ = figure.build(self._records(1.15, 0.76), margin=0.32)
        self.assertAlmostEqual(fits["shuffle_early_N4"][0], 1.15, places=6)
        self.assertAlmostEqual(fits["shuffle_late_N4"][0], 0.76, places=6)

    def test_every_condition_in_the_style_table_has_a_validated_colour(self):
        # The palette passed the six colour checks as a set; a condition added later without
        # revalidating would silently inherit an unchecked hue.
        self.assertEqual(set(figure.STYLE), set(figure.ORDER))
        self.assertEqual(len({colour for colour, *_ in figure.STYLE.values()}), len(figure.ORDER))


if __name__ == "__main__":
    unittest.main()

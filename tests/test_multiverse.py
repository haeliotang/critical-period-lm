"""Tests for the robustness exhibit.

The exhibit is only worth anything if its frozen cell is the frozen analysis. If
`verdict_under` at the frozen specification disagreed with `study_verdict`, the grid would be
measuring some neighbouring procedure and every share in it would be uninterpretable. That is
the first test here and the reason the others exist.
"""

import importlib.util
import math
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("multiverse", ROOT / "analysis" / "multiverse.py")
multiverse = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(multiverse)

from critical_period_lm.decision_rules import (  # noqa: E402
    CRITICAL_PERIOD,
    NEGATIVE_CONTROL_PREFIX,
    REVERSE_ONSET_EFFECT,
    RunRecord,
    fit_exponent,
    study_verdict,
)

BUDGETS = (1_350, 2_700, 5_400, 10_800)
TOP = BUDGETS[-1]
BASELINE = {
    1_350: [2.61, 2.62, 2.60, 2.63, 2.615],
    2_700: [2.2844, 2.2962, 2.2893, 2.2900, 2.2945],
    5_400: [2.0307, 2.0382, 2.0290, 2.0330, 2.0432],
    10_800: [1.8544, 1.8581, 1.8545, 1.8560, 1.8648],
}
CONTROL = (1.05, 0.98, 1.02, 1.00, 1.01)
LIKE = (1.03, 0.99, 1.01, 1.02, 1.00)
SLOW = (0.55, 0.50, 0.52, 0.48, 0.51)


def gaps_for(alphas, top_gap=0.05):
    return {b: [top_gap * (TOP / b) ** a for a in alphas] for b in BUDGETS}


def build(early, late, control=CONTROL):
    records = [
        RunRecord("baseline", seed, loss, budget)
        for budget, losses in BASELINE.items()
        for seed, loss in enumerate(losses)
    ]
    for condition, alphas in (
        ("shuffle_early_N4", early), ("shuffle_late_N4", late), ("fixed_early_N4", control)
    ):
        for budget, values in gaps_for(alphas).items():
            for seed, gap in enumerate(values):
                records.append(RunRecord(condition, seed, BASELINE[budget][seed] + gap, budget))
    return records


class FrozenCellTests(unittest.TestCase):
    """The frozen cell must be the frozen analysis, on every shape the study can produce."""

    def test_the_frozen_specification_reproduces_the_frozen_code(self):
        for label, early, late in (
            ("critical period", SLOW, LIKE),
            ("reverse effect", LIKE, SLOW),
            ("no onset effect", LIKE, (1.02, 1.00, 0.99, 1.03, 1.01)),
        ):
            with self.subTest(label):
                records = build(early, late)
                mine, *_ = multiverse.verdict_under(records, multiverse.FROZEN)
                self.assertEqual(mine, study_verdict(records).verdict)

    def test_the_frozen_specification_is_actually_in_the_grid(self):
        self.assertIn(multiverse.FROZEN, list(multiverse.enumerate_specs()))

    def test_the_grid_is_the_product_of_its_dimensions(self):
        expected = (
            len(multiverse.SCALES) * len(multiverse.MULTIPLES) * len(multiverse.FLOORS)
            * len(multiverse.ESTIMATORS) * len(multiverse.RUNGS)
        )
        self.assertEqual(len(list(multiverse.enumerate_specs())), expected)


class ExclusionTests(unittest.TestCase):
    """The excluded half is the half that makes a multiverse mean anything."""

    def test_every_exclusion_carries_a_reason(self):
        self.assertGreaterEqual(len(multiverse.EXCLUSIONS), 4)
        for what, why in multiverse.EXCLUSIONS:
            self.assertTrue(what.strip() and why.strip())

    def test_the_refuted_theoretical_anchor_is_not_a_scale_option(self):
        # Reading the exponent against 1 is the design v3 defect. It does not get a vote.
        self.assertNotIn("theory", multiverse.SCALES)
        self.assertTrue(any("theoretical value 1" in what for what, _ in multiverse.EXCLUSIONS))

    def test_outlier_dropping_is_excluded_by_name(self):
        self.assertTrue(any("outlier seed" in what for what, _ in multiverse.EXCLUSIONS))


class EstimatorTests(unittest.TestCase):
    def test_theil_sen_recovers_a_planted_exponent(self):
        for planted in (0.5, 1.0, 1.5):
            gaps = [0.05 * (TOP / b) ** planted for b in BUDGETS]
            self.assertAlmostEqual(
                multiverse.theil_sen_exponent(list(BUDGETS), gaps), planted, places=9
            )

    def test_theil_sen_is_the_more_robust_of_the_two(self):
        # One corrupted rung is exactly the failure mode that produced the v4 control's 1.505.
        clean = [0.05 * (TOP / b) ** 1.0 for b in BUDGETS]
        spoiled = list(clean)
        spoiled[-1] *= 0.5
        ols_shift = abs(fit_exponent(list(BUDGETS), spoiled) - 1.0)
        sen_shift = abs(multiverse.theil_sen_exponent(list(BUDGETS), spoiled) - 1.0)
        self.assertLess(sen_shift, ols_shift)

    def test_a_non_positive_gap_is_refused_by_both(self):
        with self.assertRaises(ValueError):
            multiverse.theil_sen_exponent(list(BUDGETS), [0.05, 0.02, 0.0, 0.01])


class ScaleTests(unittest.TestCase):
    def test_pooling_uses_conditions_the_control_only_scale_ignores(self):
        alphas = {
            "fixed_early_N4": [1.0, 1.5, 1.0, 1.4, 1.1],   # noisy
            "shuffle_early_N4": [1.0, 1.01, 0.99, 1.0, 1.0],
            "shuffle_late_N4": [0.76, 0.76, 0.75, 0.77, 0.76],
        }
        control_only = multiverse.margin_from("control", alphas, 3.0, 0.0)
        pooled = multiverse.margin_from("pooled-all", alphas, 3.0, 0.0)
        arms = multiverse.margin_from("pooled-arms", alphas, 3.0, 0.0)
        self.assertGreater(control_only, pooled)
        self.assertGreater(pooled, arms)

    def test_the_floor_binds_when_the_scale_is_tiny(self):
        alphas = {c: [1.0, 1.0, 1.0, 1.0, 1.0] for c in
                  ("fixed_early_N4", "shuffle_early_N4", "shuffle_late_N4")}
        self.assertAlmostEqual(multiverse.margin_from("control", alphas, 3.0, 0.10), 0.10)

    def test_mad_resists_a_single_outlying_seed(self):
        alphas = {"fixed_early_N4": [1.10, 1.15, 1.12, 1.14, 1.90]}
        sd_based = multiverse.margin_from("control", alphas, 3.0, 0.0)
        mad_based = multiverse.margin_from("mad-control", alphas, 3.0, 0.0)
        self.assertLess(mad_based, sd_based)


class ReportTests(unittest.TestCase):
    def test_the_report_says_it_is_not_a_result(self):
        records = build(LIKE, SLOW)
        text = multiverse.report("test", records, REVERSE_ONSET_EFFECT)
        self.assertIn("NOT A RESULT", text)
        self.assertIn("nothing here revises it", text)

    def test_the_report_flags_a_frozen_cell_that_disagrees(self):
        # If the grid's frozen cell ever stops matching the registered verdict, the exhibit
        # must say so loudly rather than quietly reporting shares.
        records = build(SLOW, LIKE)
        text = multiverse.report("test", records, REVERSE_ONSET_EFFECT)
        self.assertIn("NO — investigate", text)

    def test_the_report_names_every_exclusion(self):
        records = build(LIKE, SLOW)
        text = multiverse.report("test", records, REVERSE_ONSET_EFFECT)
        for what, _ in multiverse.EXCLUSIONS:
            self.assertIn(what, text)

    def test_a_planted_critical_period_is_stable_across_the_grid(self):
        records = build(SLOW, LIKE)
        verdicts = [multiverse.verdict_under(records, s)[0] for s in multiverse.enumerate_specs()]
        share = verdicts.count(CRITICAL_PERIOD) / len(verdicts)
        self.assertGreater(share, 0.8)


if __name__ == "__main__":
    unittest.main()

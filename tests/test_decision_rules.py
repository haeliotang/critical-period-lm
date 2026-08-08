"""Rehearsal gate for the frozen decision rules.

Section 7.2 of the preregistration: the decision code must return the right answer on
fabricated records whose truth is known, for every outcome it can return, before it is
allowed to see a real run. A judgment rule that has never been run against a known answer is
not a registered rule.

The endpoint is an estimated decay exponent, so the planted truths here are exponents. Gaps
are constructed as `gap(T) = top_gap · (T_top/T)^a` with `a` chosen per seed, which makes
each seed's fitted exponent exactly the planted one and every fixture legible as a claim
about decay rather than as a list of numbers.
"""

import math
import unittest

from critical_period_lm.decision_rules import (
    ALPHA,
    CRITICAL_PERIOD,
    DESIGN_FAILURE,
    INCONCLUSIVE,
    LAG,
    NO_CRITICAL_PERIOD,
    NO_EFFECT,
    PERSISTENT,
    REVERSE_ONSET_EFFECT,
    SUBLINEAR,
    UNDETERMINED,
    RunRecord,
    crossing_budget,
    exact_permutation_p,
    fit_condition,
    fit_exponent,
    level_margin,
    paired_gaps,
    study_verdict,
    t_interval,
)

BUDGETS = (2_700, 5_400, 10_800)
TOP = BUDGETS[-1]

# Baseline falls with budget, as it does in reality, with a spread that leaves the level
# margin on its 0.01 floor.
BASELINE = {
    2_700: [2.2844, 2.2962, 2.2893, 2.2900],
    5_400: [2.0307, 2.0382, 2.0290, 2.0330],
    10_800: [1.8544, 1.8581, 1.8545, 1.8560],
}

LAG_ALPHAS = (1.05, 0.98, 1.02, 1.00)
SUBLINEAR_ALPHAS = (0.55, 0.50, 0.52, 0.48)
FLAT_ALPHAS = (0.05, 0.02, -0.01, 0.03)
WILD_ALPHAS = (1.20, 0.10, 0.80, 0.30)


def gaps_for(alphas, top_gap=0.05):
    """Gaps whose per-seed fitted exponent is exactly the planted one."""
    return {b: [top_gap * (TOP / b) ** a for a in alphas] for b in BUDGETS}


def build_ladder(gaps_by_condition, baseline=BASELINE):
    records = [
        RunRecord("baseline", seed, loss, budget)
        for budget, losses in baseline.items()
        for seed, loss in enumerate(losses)
    ]
    for condition, by_budget in gaps_by_condition.items():
        for budget, gaps in by_budget.items():
            for seed, gap in enumerate(gaps):
                records.append(
                    RunRecord(condition, seed, baseline[budget][seed] + gap, budget)
                )
    return records


class ExponentFittingTests(unittest.TestCase):
    def test_a_planted_exponent_is_recovered_exactly(self):
        for planted in (0.0, 0.5, 1.0, 1.5):
            gaps = [0.05 * (TOP / b) ** planted for b in BUDGETS]
            self.assertAlmostEqual(fit_exponent(list(BUDGETS), gaps), planted, places=9)

    def test_a_pure_lag_gives_exponent_one(self):
        # gap = c/T is what lost training alone predicts.
        gaps = [270.0 / b for b in BUDGETS]
        self.assertAlmostEqual(fit_exponent(list(BUDGETS), gaps), 1.0, places=9)

    def test_a_frozen_gap_gives_exponent_zero(self):
        gaps = [0.05, 0.05, 0.05]
        self.assertAlmostEqual(fit_exponent(list(BUDGETS), gaps), 0.0, places=9)

    def test_a_non_positive_gap_is_refused_rather_than_nudged(self):
        with self.assertRaises(ValueError):
            fit_exponent(list(BUDGETS), [0.05, 0.0, 0.01])
        with self.assertRaises(ValueError):
            fit_exponent(list(BUDGETS), [0.05, -0.001, 0.01])

    def test_one_rung_is_an_error(self):
        with self.assertRaises(ValueError):
            fit_exponent([5_400], [0.05])


class CrossingBudgetTests(unittest.TestCase):
    def test_a_pure_lag_crosses_where_the_law_says(self):
        # gap = 270/T reaches 0.01 at T = 27,000.
        gaps = [270.0 / b for b in BUDGETS]
        self.assertAlmostEqual(crossing_budget(list(BUDGETS), gaps, 0.01), 27_000, places=3)

    def test_the_power_law_does_not_reproduce_the_log_linear_defect(self):
        # Ladder 1's mean late-arm gaps. The retired log-linear form put the crossing near
        # 14,900 and predicted a negative gap one rung out; the power law puts it past
        # 20,000 and stays positive everywhere.
        gaps = [0.0644, 0.0376, 0.0218]
        crossing = crossing_budget(list(BUDGETS), gaps, 0.01)
        self.assertGreater(crossing, 20_000)
        self.assertTrue(math.isfinite(crossing))

    def test_a_frozen_gap_never_crosses(self):
        self.assertEqual(crossing_budget(list(BUDGETS), [0.05, 0.05, 0.05], 0.01), math.inf)


class IntervalTests(unittest.TestCase):
    def test_the_interval_widens_as_seeds_disagree(self):
        _, tight_low, tight_high = t_interval([1.00, 1.01, 0.99, 1.00])
        _, wide_low, wide_high = t_interval([1.40, 0.60, 1.20, 0.80])
        self.assertLess(tight_high - tight_low, wide_high - wide_low)

    def test_a_single_seed_yields_no_interval(self):
        _, low, high = t_interval([1.0])
        self.assertEqual((low, high), (-math.inf, math.inf))


class PermutationTests(unittest.TestCase):
    def test_complete_separation_reaches_the_floor(self):
        self.assertAlmostEqual(
            exact_permutation_p([2.0, 2.1, 2.2, 2.3], [1.0, 1.1, 1.2, 1.3]), 1 / 70
        )

    def test_the_two_sided_test_costs_a_factor_of_two(self):
        one = exact_permutation_p([2.0, 2.1, 2.2, 2.3], [1.0, 1.1, 1.2, 1.3])
        two = exact_permutation_p(
            [2.0, 2.1, 2.2, 2.3], [1.0, 1.1, 1.2, 1.3], two_sided=True
        )
        self.assertAlmostEqual(two, 2 * one)

    def test_the_two_sided_test_sees_an_effect_the_one_sided_one_misses(self):
        low, high = [1.0, 1.1, 1.2, 1.3], [2.0, 2.1, 2.2, 2.3]
        self.assertAlmostEqual(exact_permutation_p(low, high), 1.0)
        self.assertLessEqual(exact_permutation_p(low, high, two_sided=True), ALPHA)


class ReadingTests(unittest.TestCase):
    level = 0.01

    def _read(self, alphas, top_gap=0.05):
        gaps = paired_gaps(build_ladder({"c": gaps_for(alphas, top_gap)}))
        return fit_condition("c", gaps["c"], self.level)

    def test_decay_at_the_lag_rate_reads_lag(self):
        fit = self._read(LAG_ALPHAS)
        self.assertEqual(fit.reading, LAG)
        self.assertLessEqual(fit.alpha_low, 1.0)
        self.assertGreaterEqual(fit.alpha_high, 1.0)
        self.assertIn("pure lost training", fit.label)

    def test_decay_slower_than_a_lag_reads_sublinear(self):
        fit = self._read(SUBLINEAR_ALPHAS)
        self.assertEqual(fit.reading, SUBLINEAR)
        self.assertLess(fit.alpha_high, 1.0)
        self.assertGreater(fit.alpha_low, 0.0)

    def test_a_gap_that_does_not_move_reads_persistent(self):
        self.assertEqual(self._read(FLAT_ALPHAS).reading, PERSISTENT)

    def test_seeds_that_disagree_wildly_settle_nothing(self):
        self.assertEqual(self._read(WILD_ALPHAS).reading, UNDETERMINED)

    def test_damage_under_the_level_floor_is_not_modelled(self):
        # Fitting a decay law to noise around zero would invent a number.
        fit = self._read(LAG_ALPHAS, top_gap=0.002)
        self.assertEqual(fit.reading, NO_EFFECT)
        self.assertTrue(math.isnan(fit.alpha))

    def test_a_seed_whose_gap_goes_non_positive_is_dropped_not_nudged(self):
        gaps = paired_gaps(build_ladder({"c": gaps_for(LAG_ALPHAS)}))
        gaps["c"][TOP][0] = -0.001
        fit = fit_condition("c", gaps["c"], self.level)
        self.assertEqual(fit.seeds_dropped, 1)
        self.assertEqual(fit.seeds_fitted, len(LAG_ALPHAS) - 1)


class StudyRehearsalTests(unittest.TestCase):
    """Every verdict the study can return, each against a planted truth."""

    def _verdict(self, early, late, control=LAG_ALPHAS):
        return study_verdict(
            build_ladder(
                {
                    "shuffle_early_N4": gaps_for(early),
                    "shuffle_late_N4": gaps_for(late),
                    "fixed_early_N4": gaps_for(control),
                }
            )
        )

    def test_early_damage_decaying_more_slowly_is_a_critical_period(self):
        result = self._verdict(early=SUBLINEAR_ALPHAS, late=LAG_ALPHAS)
        self.assertEqual(result.verdict, CRITICAL_PERIOD)
        self.assertLessEqual(result.primary_p_one_sided, ALPHA)
        self.assertLess(result.primary_delta, -result.exponent_margin)

    def test_late_damage_decaying_more_slowly_is_the_reverse_effect(self):
        # The shape ladder 1 pointed at. It must have a name, or it would be absorbed into
        # a null and the most interesting thing in the data would go unreported.
        result = self._verdict(early=LAG_ALPHAS, late=SUBLINEAR_ALPHAS)
        self.assertEqual(result.verdict, REVERSE_ONSET_EFFECT)
        self.assertGreater(result.primary_delta, result.exponent_margin)
        self.assertLessEqual(result.primary_p_two_sided, ALPHA)
        self.assertTrue(any("opposite to a critical period" in r for r in result.reasons))

    def test_onset_making_no_difference_is_no_critical_period(self):
        result = self._verdict(early=LAG_ALPHAS, late=(1.03, 1.00, 0.99, 1.04))
        self.assertEqual(result.verdict, NO_CRITICAL_PERIOD)
        self.assertLess(abs(result.primary_delta), result.exponent_margin)
        self.assertTrue(any("repairable rather than permanent" in r for r in result.reasons))

    def test_a_control_that_is_not_a_pure_lag_is_a_design_failure(self):
        result = self._verdict(
            early=SUBLINEAR_ALPHAS, late=LAG_ALPHAS, control=SUBLINEAR_ALPHAS
        )
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("does not behave as a pure lag" in r for r in result.reasons))

    def test_design_failure_outranks_a_planted_critical_period(self):
        # The control is read before the primary contrast, so a planted effect cannot
        # rescue a design whose measurement misbehaves.
        result = self._verdict(early=FLAT_ALPHAS, late=LAG_ALPHAS, control=FLAT_ALPHAS)
        self.assertEqual(result.verdict, DESIGN_FAILURE)

    def test_a_difference_too_noisy_to_place_is_inconclusive(self):
        result = self._verdict(early=(1.20, 0.90, 1.10, 1.00), late=(0.85, 0.75, 0.95, 0.80))
        self.assertEqual(result.verdict, INCONCLUSIVE)

    def test_the_exponent_margin_comes_from_the_control(self):
        tight = self._verdict(early=LAG_ALPHAS, late=LAG_ALPHAS, control=(1.00, 1.01, 0.99, 1.00))
        loose = self._verdict(early=LAG_ALPHAS, late=LAG_ALPHAS, control=(1.30, 0.70, 1.20, 0.80))
        self.assertLess(tight.exponent_margin, loose.exponent_margin)
        self.assertGreaterEqual(tight.exponent_margin, 0.10)


class MechanicalGateTests(unittest.TestCase):
    def _full(self):
        return {
            "shuffle_early_N4": gaps_for(LAG_ALPHAS),
            "shuffle_late_N4": gaps_for(LAG_ALPHAS),
            "fixed_early_N4": gaps_for(LAG_ALPHAS),
        }

    def test_a_single_budget_is_a_design_failure(self):
        records = [r for r in build_ladder(self._full()) if r.total_steps == 2_700]
        result = study_verdict(records)
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("two budget rungs" in r for r in result.reasons))

    def test_a_diverged_run_is_a_design_failure(self):
        records = build_ladder(self._full())
        records[0] = RunRecord("baseline", 0, math.nan, 2_700)
        result = study_verdict(records)
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("non-finite" in r for r in result.reasons))

    def test_a_missing_negative_control_is_a_design_failure(self):
        gaps = self._full()
        del gaps["fixed_early_N4"]
        result = study_verdict(build_ladder(gaps))
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("no negative control" in r for r in result.reasons))


class MarginTests(unittest.TestCase):
    def test_level_margin_uses_the_floor_when_baseline_variance_is_tiny(self):
        self.assertAlmostEqual(level_margin([1.0, 1.0001, 0.9999, 1.0]), 0.01)

    def test_level_margin_uses_three_baseline_sd_when_variance_is_large(self):
        self.assertGreater(level_margin([0.90, 1.10, 0.95, 1.05]), 0.01)


if __name__ == "__main__":
    unittest.main()

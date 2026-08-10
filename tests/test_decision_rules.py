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
    ANCHOR,
    CRITICAL_PERIOD,
    DESIGN_FAILURE,
    FASTER_THAN_CONTROL,
    INCONCLUSIVE,
    LIKE_CONTROL,
    NO_CRITICAL_PERIOD,
    NO_EFFECT,
    REVERSE_ONSET_EFFECT,
    SLOWER_THAN_CONTROL,
    RunRecord,
    baseline_log_slopes,
    exact_permutation_p,
    fit_condition,
    fit_exponent,
    implied_pure_lag_exponent,
    level_margin,
    paired_gaps,
    study_verdict,
    t_interval,
)

BUDGETS = (2_700, 5_400, 10_800)
TOP = BUDGETS[-1]

# Baseline falls with budget, as it does in reality, with a spread that leaves the level
# margin on its 0.01 floor.
# The measured shape: the log-slope falls between rungs, which is exactly the fact that
# makes a theoretical anchor of alpha = 1 wrong.
BASELINE = {
    2_700: [2.2844, 2.2962, 2.2893, 2.2900, 2.2945],
    5_400: [2.0307, 2.0382, 2.0290, 2.0330, 2.0432],
    10_800: [1.8544, 1.8581, 1.8545, 1.8560, 1.8648],
}

# Five seeds, as Section 4.3 requires: the two-sided permutation floor is 0.100 at three
# seeds and 0.008 at five, and the design needs to be able to reject.
CONTROL_ALPHAS = (1.05, 0.98, 1.02, 1.00, 1.01)
LIKE_ALPHAS = (1.03, 0.99, 1.01, 1.02, 1.00)
SLOW_ALPHAS = (0.55, 0.50, 0.52, 0.48, 0.51)
FAST_ALPHAS = (1.55, 1.50, 1.52, 1.48, 1.51)
WILD_ALPHAS = (1.20, 0.10, 0.80, 0.30, 1.40)


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


class DescriptiveAnchorTests(unittest.TestCase):
    """The naive anchor is reported, never gated on."""

    def test_the_baseline_log_slope_is_measured_and_falls(self):
        means = {b: sum(v) / len(v) for b, v in BASELINE.items()}
        slopes = baseline_log_slopes(means)
        self.assertEqual(len(slopes), 2)
        self.assertLess(slopes[1], slopes[0])

    def test_a_falling_slope_puts_the_pure_lag_anchor_above_one(self):
        # gap = b(T)*delta/T, so a falling b makes a pure lag decay faster than 1/T. This is
        # why alpha = 1 was the wrong gate; the corrected value is reported, not enforced.
        means = {b: sum(v) / len(v) for b, v in BASELINE.items()}
        implied = implied_pure_lag_exponent(baseline_log_slopes(means), BUDGETS)
        self.assertGreater(implied, 1.0)


class ReadingTests(unittest.TestCase):
    """Readings are taken against the control, not against theory."""

    def _readings(self, **conditions):
        result = study_verdict(build_ladder({k: gaps_for(v) for k, v in conditions.items()}))
        return {f.condition: f.reading for f in result.fits}, result

    def test_the_control_is_the_anchor(self):
        readings, _ = self._readings(
            fixed_early_N4=CONTROL_ALPHAS,
            shuffle_early_N4=LIKE_ALPHAS,
            shuffle_late_N4=LIKE_ALPHAS,
        )
        self.assertEqual(readings["fixed_early_N4"], ANCHOR)

    def test_a_condition_matching_the_control_reads_like_control(self):
        readings, _ = self._readings(
            fixed_early_N4=CONTROL_ALPHAS,
            shuffle_early_N4=LIKE_ALPHAS,
            shuffle_late_N4=LIKE_ALPHAS,
        )
        self.assertEqual(readings["shuffle_early_N4"], LIKE_CONTROL)

    def test_a_condition_repairing_more_slowly_reads_slower(self):
        readings, _ = self._readings(
            fixed_early_N4=CONTROL_ALPHAS,
            shuffle_early_N4=LIKE_ALPHAS,
            shuffle_late_N4=SLOW_ALPHAS,
        )
        self.assertEqual(readings["shuffle_late_N4"], SLOWER_THAN_CONTROL)

    def test_a_condition_repairing_faster_reads_faster(self):
        readings, _ = self._readings(
            fixed_early_N4=CONTROL_ALPHAS,
            shuffle_early_N4=FAST_ALPHAS,
            shuffle_late_N4=LIKE_ALPHAS,
        )
        self.assertEqual(readings["shuffle_early_N4"], FASTER_THAN_CONTROL)

    def test_a_control_far_from_one_no_longer_fails_the_design(self):
        # The ladder-2 lesson, pinned. A control at 1.5 is simply the anchor; the design
        # used to call this a failure because it required the control to sit on alpha = 1.
        readings, result = self._readings(
            fixed_early_N4=FAST_ALPHAS,
            shuffle_early_N4=FAST_ALPHAS,
            shuffle_late_N4=SLOW_ALPHAS,
        )
        self.assertEqual(readings["fixed_early_N4"], ANCHOR)
        self.assertNotEqual(result.verdict, DESIGN_FAILURE)

    def test_damage_under_the_level_floor_is_not_modelled(self):
        records = build_ladder(
            {
                "fixed_early_N4": gaps_for(CONTROL_ALPHAS),
                "shuffle_early_N4": gaps_for(LIKE_ALPHAS, top_gap=0.002),
                "shuffle_late_N4": gaps_for(LIKE_ALPHAS),
            }
        )
        readings = {f.condition: f.reading for f in study_verdict(records).fits}
        self.assertEqual(readings["shuffle_early_N4"], NO_EFFECT)

    def test_a_seed_whose_gap_goes_non_positive_is_dropped_not_nudged(self):
        gaps = paired_gaps(build_ladder({"c": gaps_for(CONTROL_ALPHAS)}))
        gaps["c"][TOP][0] = -0.001
        fit = fit_condition("c", gaps["c"], 0.01)
        self.assertEqual(fit.seeds_dropped, 1)
        self.assertEqual(fit.seeds_fitted, len(CONTROL_ALPHAS) - 1)


class StudyRehearsalTests(unittest.TestCase):
    """Every verdict the study can return, each against a planted truth."""

    def _verdict(self, early, late, control=CONTROL_ALPHAS):
        return study_verdict(
            build_ladder(
                {
                    "shuffle_early_N4": gaps_for(early),
                    "shuffle_late_N4": gaps_for(late),
                    "fixed_early_N4": gaps_for(control),
                }
            )
        )

    def test_early_damage_repairing_more_slowly_is_a_critical_period(self):
        result = self._verdict(early=SLOW_ALPHAS, late=LIKE_ALPHAS)
        self.assertEqual(result.verdict, CRITICAL_PERIOD)
        self.assertLessEqual(result.primary_p_one_sided, ALPHA)
        self.assertLess(result.primary_delta, -result.exponent_margin)

    def test_late_damage_repairing_more_slowly_is_the_reverse_effect(self):
        # The shape ladders 1 and 2 both pointed at. It must have a name, or it would be
        # absorbed into a null and the most interesting thing in the data would go unsaid.
        result = self._verdict(early=LIKE_ALPHAS, late=SLOW_ALPHAS)
        self.assertEqual(result.verdict, REVERSE_ONSET_EFFECT)
        self.assertGreater(result.primary_delta, result.exponent_margin)
        self.assertLessEqual(result.primary_p_two_sided, ALPHA)
        self.assertTrue(any("opposite to a critical period" in r for r in result.reasons))

    def test_onset_making_no_difference_is_no_critical_period(self):
        result = self._verdict(early=LIKE_ALPHAS, late=(1.02, 1.00, 0.99, 1.03, 1.01))
        self.assertEqual(result.verdict, NO_CRITICAL_PERIOD)
        self.assertLess(abs(result.primary_delta), result.exponent_margin)
        self.assertTrue(any("same rate" in r for r in result.reasons))

    def test_a_missing_control_is_a_design_failure(self):
        result = study_verdict(
            build_ladder(
                {"shuffle_early_N4": gaps_for(LIKE_ALPHAS), "shuffle_late_N4": gaps_for(SLOW_ALPHAS)}
            )
        )
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("no usable negative control" in r for r in result.reasons))

    def test_a_control_with_no_damage_cannot_anchor(self):
        result = self._verdict(
            early=LIKE_ALPHAS, late=SLOW_ALPHAS, control=CONTROL_ALPHAS
        )
        self.assertNotEqual(result.verdict, DESIGN_FAILURE)
        broken = study_verdict(
            build_ladder(
                {
                    "shuffle_early_N4": gaps_for(LIKE_ALPHAS),
                    "shuffle_late_N4": gaps_for(SLOW_ALPHAS),
                    "fixed_early_N4": gaps_for(CONTROL_ALPHAS, top_gap=0.002),
                }
            )
        )
        self.assertEqual(broken.verdict, DESIGN_FAILURE)

    def test_a_difference_too_noisy_to_place_is_inconclusive(self):
        result = self._verdict(
            early=(1.30, 0.90, 1.10, 1.00, 1.35), late=(0.85, 0.75, 1.20, 0.80, 1.15)
        )
        self.assertEqual(result.verdict, INCONCLUSIVE)

    def test_the_exponent_margin_comes_from_the_control(self):
        tight = self._verdict(LIKE_ALPHAS, LIKE_ALPHAS, control=(1.00, 1.01, 0.99, 1.00, 1.00))
        loose = self._verdict(LIKE_ALPHAS, LIKE_ALPHAS, control=(1.30, 0.70, 1.20, 0.80, 1.00))
        self.assertLess(tight.exponent_margin, loose.exponent_margin)
        self.assertGreaterEqual(tight.exponent_margin, 0.10)

    def test_the_naive_anchor_is_reported_but_gates_nothing(self):
        result = self._verdict(early=LIKE_ALPHAS, late=SLOW_ALPHAS)
        self.assertEqual(len(result.baseline_log_slopes), len(BUDGETS) - 1)
        self.assertTrue(math.isfinite(result.implied_pure_lag_exponent))
        self.assertEqual(result.verdict, REVERSE_ONSET_EFFECT)


class MechanicalGateTests(unittest.TestCase):
    def _full(self):
        return {
            "shuffle_early_N4": gaps_for(LIKE_ALPHAS),
            "shuffle_late_N4": gaps_for(LIKE_ALPHAS),
            "fixed_early_N4": gaps_for(CONTROL_ALPHAS),
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


class MarginTests(unittest.TestCase):
    def test_level_margin_uses_the_floor_when_baseline_variance_is_tiny(self):
        self.assertAlmostEqual(level_margin([1.0, 1.0001, 0.9999, 1.0]), 0.01)

    def test_level_margin_uses_three_baseline_sd_when_variance_is_large(self):
        self.assertGreater(level_margin([0.90, 1.10, 0.95, 1.05]), 0.01)


if __name__ == "__main__":
    unittest.main()

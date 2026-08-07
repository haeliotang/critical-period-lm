"""Rehearsal gate for the frozen decision rules.

Section 7.2 of the preregistration: the decision code must return the right verdict on
fabricated records whose answer is known, for every verdict it is capable of returning,
before it is allowed to see a real run. A judgment rule that has never been run against a
known answer is not a registered rule.

The endpoint is a decay across a ladder of budgets, so the planted ground truths here are
shapes rather than levels: a gap that stays flat as the budget grows is permanent damage, a
gap that shrinks is unfinished recovery. Every number is written out rather than sampled, so
a failure here is a change in the rules and never a change in a random draw.
"""

import math
import unittest

from critical_period_lm.decision_rules import (
    ALPHA,
    CRITICAL_PERIOD,
    DECAYING_UNRESOLVED,
    DESIGN_FAILURE,
    INCONCLUSIVE,
    NO_CRITICAL_PERIOD,
    NO_EFFECT,
    PERSISTENT,
    TRANSIENT,
    RunRecord,
    decay_slope_test,
    exact_permutation_p,
    ladder_verdict,
    minimum_detectable_effect,
    paired_gaps,
    registered_margin,
    study_verdict,
)

BUDGETS = (5_400, 10_800, 21_600)

# Three seeds per rung. The baseline falls with budget, as it does in reality.
BASELINE = {
    5_400: [2.0300, 2.0360, 2.0330],
    10_800: [1.8540, 1.8600, 1.8570],
    21_600: [1.7000, 1.7060, 1.7030],
}

FLAT = {5_400: [0.050, 0.052, 0.048], 10_800: [0.051, 0.049, 0.050], 21_600: [0.049, 0.051, 0.050]}
DECAYS = {5_400: [0.050, 0.052, 0.048], 10_800: [0.020, 0.021, 0.019], 21_600: [0.004, 0.005, 0.003]}
# Small and flat. A small gap that is still visibly shrinking is TRANSIENT, not NO_EFFECT:
# the distinction is whether a trend is detectable, not whether the gap is little.
TINY = {5_400: [0.003, 0.005, 0.002], 10_800: [0.004, 0.002, 0.005], 21_600: [0.002, 0.005, 0.003]}


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


class DecayTestTests(unittest.TestCase):
    def test_a_clearly_shrinking_gap_gives_a_negative_slope_and_rejects(self):
        budgets = [b for b in BUDGETS for _ in range(3)]
        gaps = [g for b in BUDGETS for g in DECAYS[b]]
        slope, p = decay_slope_test(budgets, gaps)
        self.assertLess(slope, 0)
        self.assertLessEqual(p, ALPHA)

    def test_a_flat_gap_does_not_reject(self):
        budgets = [b for b in BUDGETS for _ in range(3)]
        gaps = [g for b in BUDGETS for g in FLAT[b]]
        slope, p = decay_slope_test(budgets, gaps)
        self.assertGreater(p, ALPHA)
        self.assertLess(abs(slope), 0.005)

    def test_a_growing_gap_gives_a_p_value_near_one(self):
        budgets = [b for b in BUDGETS for _ in range(3)]
        gaps = [g for b in reversed(BUDGETS) for g in DECAYS[b]]
        slope, p = decay_slope_test(budgets, gaps)
        self.assertGreater(slope, 0)
        self.assertGreater(p, 0.9)

    def test_three_rungs_of_three_seeds_can_reach_significance(self):
        # 9!/(3!3!3!) = 1680 distinct budget-label assignments, so the floor is 1/1680.
        # A paired sign-flip test at three seeds bottoms out at 1/8 and could never reject.
        budgets = [b for b in BUDGETS for _ in range(3)]
        gaps = [0.10, 0.10, 0.10, 0.05, 0.05, 0.05, 0.01, 0.01, 0.01]
        _, p = decay_slope_test(budgets, gaps)
        self.assertAlmostEqual(p, 1 / 1680, places=6)

    def test_one_rung_is_an_error_not_a_slope(self):
        with self.assertRaises(ValueError):
            decay_slope_test([5_400, 5_400, 5_400], [0.05, 0.04, 0.06])


class PairingTests(unittest.TestCase):
    def test_gaps_are_taken_against_the_same_seed_at_the_same_budget(self):
        records = build_ladder({"shuffle_early_N4": DECAYS})
        gaps = paired_gaps(records)
        for budget in BUDGETS:
            for seed, gap in gaps["shuffle_early_N4"][budget].items():
                self.assertAlmostEqual(gap, DECAYS[budget][seed], places=9)

    def test_a_deficit_run_without_its_baseline_partner_is_dropped(self):
        records = [r for r in build_ladder({"shuffle_early_N4": DECAYS})
                   if not (r.condition == "baseline" and r.total_steps == 21_600 and r.seed == 0)]
        gaps = paired_gaps(records)
        self.assertNotIn(0, gaps["shuffle_early_N4"][21_600])
        self.assertIn(1, gaps["shuffle_early_N4"][21_600])


class LadderVerdictTests(unittest.TestCase):
    margin = 0.01

    def _verdict(self, shape):
        gaps = paired_gaps(build_ladder({"c": shape}))
        return ladder_verdict("c", gaps["c"], self.margin)

    def test_a_gap_that_stays_put_is_persistent(self):
        self.assertEqual(self._verdict(FLAT).verdict, PERSISTENT)

    def test_a_gap_that_decays_under_the_margin_is_transient(self):
        self.assertEqual(self._verdict(DECAYS).verdict, TRANSIENT)

    def test_a_gap_under_the_margin_throughout_is_no_effect(self):
        self.assertEqual(self._verdict(TINY).verdict, NO_EFFECT)

    def test_a_shrinking_but_still_large_gap_is_unresolved_and_extrapolated(self):
        shape = {5_400: [0.20, 0.21, 0.19], 10_800: [0.14, 0.15, 0.13], 21_600: [0.09, 0.10, 0.08]}
        result = self._verdict(shape)
        self.assertEqual(result.verdict, DECAYING_UNRESOLVED)
        self.assertGreater(result.crossing_budget, 21_600)
        self.assertIn("reaches the margin near", result.label)


class StudyRehearsalTests(unittest.TestCase):
    """Every verdict the study can return, each against a planted ground truth."""

    def test_persistent_early_damage_and_a_transient_late_one_is_a_critical_period(self):
        result = study_verdict(
            build_ladder(
                {
                    "shuffle_early_N4": FLAT,
                    "shuffle_late_N4": DECAYS,
                    "fixed_early_N4": DECAYS,
                }
            )
        )
        self.assertEqual(result.verdict, CRITICAL_PERIOD)
        self.assertGreaterEqual(result.primary_delta, result.margin)
        self.assertLessEqual(result.primary_p_value, ALPHA)

    def test_damage_that_all_decays_away_is_no_critical_period(self):
        result = study_verdict(
            build_ladder(
                {
                    "shuffle_early_N4": DECAYS,
                    "shuffle_late_N4": DECAYS,
                    "fixed_early_N4": DECAYS,
                }
            )
        )
        self.assertEqual(result.verdict, NO_CRITICAL_PERIOD)
        self.assertLessEqual(result.primary_mde, result.margin)
        self.assertTrue(any("repaired by later training" in r for r in result.reasons))

    def test_a_control_whose_damage_does_not_decay_is_a_design_failure(self):
        result = study_verdict(
            build_ladder(
                {
                    "shuffle_early_N4": FLAT,
                    "shuffle_late_N4": DECAYS,
                    "fixed_early_N4": FLAT,
                }
            )
        )
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("negative control" in r for r in result.reasons))

    def test_design_failure_outranks_a_positive_primary_result(self):
        # The control is read before the primary contrast, so a planted effect cannot
        # rescue a design whose control did not behave.
        big = {5_400: [0.30, 0.31, 0.29], 10_800: [0.30, 0.29, 0.31], 21_600: [0.31, 0.30, 0.29]}
        result = study_verdict(
            build_ladder(
                {"shuffle_early_N4": big, "shuffle_late_N4": DECAYS, "fixed_early_N4": FLAT}
            )
        )
        self.assertEqual(result.verdict, DESIGN_FAILURE)

    def test_a_noisy_top_rung_is_inconclusive_not_a_null(self):
        noisy_early = {5_400: [0.06, 0.02, 0.09], 10_800: [0.05, 0.03, 0.08], 21_600: [0.05, 0.01, 0.08]}
        noisy_late = {5_400: [0.03, 0.07, 0.04], 10_800: [0.02, 0.06, 0.03], 21_600: [0.02, 0.06, 0.03]}
        result = study_verdict(
            build_ladder(
                {
                    "shuffle_early_N4": noisy_early,
                    "shuffle_late_N4": noisy_late,
                    "fixed_early_N4": DECAYS,
                }
            )
        )
        self.assertEqual(result.verdict, INCONCLUSIVE)
        self.assertGreater(result.primary_mde, result.margin)


class MechanicalGateTests(unittest.TestCase):
    def test_a_single_budget_is_a_design_failure(self):
        records = [r for r in build_ladder({"shuffle_early_N4": DECAYS}) if r.total_steps == 5_400]
        result = study_verdict(records)
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("two budget rungs" in r for r in result.reasons))

    def test_a_diverged_run_is_a_design_failure(self):
        records = build_ladder({"shuffle_early_N4": DECAYS, "fixed_early_N4": DECAYS})
        records[0] = RunRecord("baseline", 0, math.nan, 5_400)
        result = study_verdict(records)
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("non-finite" in r for r in result.reasons))

    def test_a_missing_negative_control_is_a_design_failure(self):
        result = study_verdict(
            build_ladder({"shuffle_early_N4": FLAT, "shuffle_late_N4": DECAYS})
        )
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("no negative control" in r for r in result.reasons))


class MarginAndPowerTests(unittest.TestCase):
    def test_margin_uses_the_floor_when_baseline_variance_is_tiny(self):
        self.assertAlmostEqual(registered_margin([1.0, 1.0001, 0.9999, 1.0, 1.0]), 0.01)

    def test_margin_uses_three_baseline_sd_when_variance_is_large(self):
        self.assertGreater(registered_margin([0.90, 1.10, 0.95, 1.05, 1.00]), 0.01)

    def test_complete_separation_gives_the_smallest_attainable_p(self):
        self.assertAlmostEqual(exact_permutation_p([2.0, 2.1, 2.2, 2.3], [1.0, 1.1, 1.2, 1.3]), 1 / 70)
        self.assertAlmostEqual(exact_permutation_p([2.0, 2.1, 2.2], [1.0, 1.1, 1.2]), 0.05)

    def test_an_underpowered_comparison_reports_infinite_resolution(self):
        self.assertEqual(minimum_detectable_effect([2.0, 2.1], [1.0, 1.1], margin=0.01), math.inf)

    def test_a_rejecting_comparison_could_have_detected_less_than_it_saw(self):
        mde = minimum_detectable_effect([2.0, 2.01, 2.02, 2.03], [1.0, 1.01, 1.02, 1.03], 0.01)
        self.assertLess(mde, 1.0)
        self.assertGreaterEqual(mde, 0.01)


if __name__ == "__main__":
    unittest.main()

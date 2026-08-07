"""Rehearsal gate for the frozen decision rules.

Section 7.2 of the preregistration: the decision code must return the right verdict on
fabricated records whose answer is known, for every verdict it is capable of returning,
before it is allowed to see a real run. A judgment rule that has never been run against a
known answer is not a registered rule.

The synthetic losses below are written out explicitly rather than sampled, so a failure
here is always a change in the rules and never a change in a random draw.
"""

import math
import unittest

from critical_period_lm.decision_rules import (
    ALPHA,
    CRITICAL_PERIOD,
    DESIGN_FAILURE,
    INCONCLUSIVE,
    NO_CRITICAL_PERIOD,
    RECOVERED,
    SCAR,
    RunRecord,
    cell_verdict,
    exact_permutation_p,
    minimum_detectable_effect,
    registered_margin,
    study_verdict,
)

TOTAL_STEPS = 60_000


def build_records(losses_by_condition, total_steps=TOTAL_STEPS):
    return [
        RunRecord(
            condition=condition,
            seed=index,
            final_eval_loss=loss,
            total_steps=total_steps,
        )
        for condition, losses in losses_by_condition.items()
        for index, loss in enumerate(losses)
    ]


def grid(baseline, early, late, permute, filler=None):
    """A full registered grid. Secondary cells default to baseline-like values."""
    filler = filler if filler is not None else list(baseline[:3])
    return {
        "baseline": baseline,
        "shuffle_early_N4": early,
        "shuffle_late_N4": late,
        "shuffle_early_N1": filler,
        "shuffle_late_N1": filler,
        "fixed_early_N1": permute,
        "fixed_early_N4": permute,
    }


class PermutationTestTests(unittest.TestCase):
    def test_complete_separation_gives_the_smallest_attainable_p(self):
        # 4 versus 4 enumerates C(8,4) = 70 assignments, so the floor is 1/70.
        p = exact_permutation_p([2.0, 2.1, 2.2, 2.3], [1.0, 1.1, 1.2, 1.3])
        self.assertAlmostEqual(p, 1 / 70)
        self.assertLessEqual(p, ALPHA)

        # 3 versus 3 bottoms out at 1/20 = 0.05, which is why the primary cells carry
        # four seeds: at three the test can only ever land exactly on alpha.
        self.assertAlmostEqual(exact_permutation_p([2.0, 2.1, 2.2], [1.0, 1.1, 1.2]), 0.05)

        # 2 versus 2 cannot reach alpha under any separation.
        self.assertGreater(exact_permutation_p([9.0, 9.1], [1.0, 1.1]), ALPHA)

    def test_reversed_separation_gives_the_largest_p(self):
        p = exact_permutation_p([1.0, 1.1, 1.2, 1.3], [2.0, 2.1, 2.2, 2.3])
        self.assertAlmostEqual(p, 1.0)

    def test_identical_groups_do_not_reject(self):
        p = exact_permutation_p([1.0, 1.0, 1.0, 1.0], [1.0, 1.0, 1.0, 1.0])
        self.assertAlmostEqual(p, 1.0)

    def test_p_value_is_non_increasing_in_the_shift(self):
        # The MDE bisection assumes this. Check it rather than assume it.
        treatment = [1.02, 0.97, 1.10, 0.99]
        reference = [1.00, 1.01, 0.98, 1.03, 0.995]
        previous = 1.1
        for step in range(0, 61):
            shift = step * 0.01
            p = exact_permutation_p([x + shift for x in treatment], reference)
            self.assertLessEqual(p, previous + 1e-12)
            previous = p

    def test_too_few_runs_is_an_error_not_a_p_value(self):
        with self.assertRaises(ValueError):
            exact_permutation_p([1.0], [1.0, 1.1, 1.2])


class MarginAndPowerTests(unittest.TestCase):
    def test_margin_uses_the_floor_when_baseline_variance_is_tiny(self):
        self.assertAlmostEqual(registered_margin([1.0, 1.0001, 0.9999, 1.0, 1.0]), 0.01)

    def test_margin_uses_three_baseline_sd_when_variance_is_large(self):
        baseline = [0.90, 1.10, 0.95, 1.05, 1.00]
        self.assertGreater(registered_margin(baseline), 0.01)

    def test_mde_is_never_below_the_margin(self):
        mde = minimum_detectable_effect(
            [2.0, 2.1, 2.2, 2.3], [1.0, 1.1, 1.2, 1.3], margin=0.5
        )
        self.assertGreaterEqual(mde, 0.5)

    def test_a_rejecting_cell_could_have_detected_less_than_it_saw(self):
        # A large, cleanly separated effect must not report its own size as its
        # resolution; the shift that defines the MDE is allowed to be negative.
        treatment = [2.0, 2.01, 2.02, 2.03]
        reference = [1.0, 1.01, 1.02, 1.03]
        mde = minimum_detectable_effect(treatment, reference, margin=0.01)
        self.assertLess(mde, 1.0)
        self.assertGreaterEqual(mde, 0.01)

    def test_an_underpowered_comparison_reports_infinite_resolution(self):
        self.assertEqual(
            minimum_detectable_effect([2.0, 2.1], [1.0, 1.1], margin=0.01), math.inf
        )


class CellVerdictTests(unittest.TestCase):
    baseline = [1.000, 1.004, 0.998, 1.002, 1.001]

    def test_large_separated_difference_is_a_scar(self):
        margin = registered_margin(self.baseline)
        result = cell_verdict("shuffle_early_N4", [1.20, 1.21, 1.19, 1.205], self.baseline, margin)
        self.assertEqual(result.verdict, SCAR)
        self.assertFalse(result.underpowered)

    def test_difference_below_the_margin_is_recovered(self):
        margin = registered_margin(self.baseline)
        result = cell_verdict("fixed_early_N4", [1.001, 1.003, 0.999], self.baseline, margin)
        self.assertEqual(result.verdict, RECOVERED)

    def test_large_but_unseparated_difference_is_inconclusive(self):
        # A big point estimate carried by one wild seed is not a scar.
        margin = registered_margin(self.baseline)
        result = cell_verdict("shuffle_early_N4", [1.10, 0.95, 1.25], self.baseline, margin)
        self.assertGreaterEqual(result.delta, margin)
        self.assertGreater(result.p_value, ALPHA)
        self.assertEqual(result.verdict, INCONCLUSIVE)

    def test_a_blunt_recovered_cell_is_labeled_a_calibrated_null(self):
        # No difference, but seed spread within the cell is five times the margin, so
        # this cell could not have seen the effect it is reporting the absence of.
        margin = registered_margin(self.baseline)
        result = cell_verdict("fixed_early_N4", [0.95, 1.05, 1.00], self.baseline, margin)
        self.assertEqual(result.verdict, RECOVERED)
        self.assertGreater(result.mde, margin)
        self.assertTrue(result.underpowered)
        self.assertEqual(result.label, "calibrated null (underpowered)")


class StudyRehearsalTests(unittest.TestCase):
    """The four verdicts the study can return, each against a planted ground truth."""

    def test_planted_onset_effect_returns_critical_period(self):
        result = study_verdict(
            build_records(
                grid(
                    baseline=[1.000, 1.004, 0.998, 1.002, 1.001],
                    early=[1.200, 1.210, 1.190, 1.205],
                    late=[1.050, 1.060, 1.040, 1.055],
                    permute=[1.001, 1.003, 0.999],
                )
            )
        )
        self.assertEqual(result.verdict, CRITICAL_PERIOD)
        self.assertGreater(result.primary_delta, result.margin)
        self.assertLessEqual(result.primary_p_value, ALPHA)

    def test_planted_null_with_adequate_resolution_returns_no_critical_period(self):
        result = study_verdict(
            build_records(
                grid(
                    baseline=[1.0000, 1.0020, 0.9990, 1.0010, 1.0005],
                    early=[1.0005, 1.0015, 0.9995, 1.0010],
                    late=[1.0000, 1.0020, 0.9990, 1.0012],
                    permute=[1.0000, 1.0010, 0.9995],
                )
            )
        )
        self.assertEqual(result.verdict, NO_CRITICAL_PERIOD)
        self.assertLessEqual(result.primary_mde, result.margin)

    def test_planted_null_without_resolution_returns_inconclusive(self):
        # Same absence of an onset effect, but seed spread inside the deficit cells is an
        # order of magnitude above the margin, so the study could not have seen the effect
        # it is looking for. This must not be reported as a null.
        result = study_verdict(
            build_records(
                grid(
                    baseline=[1.000, 1.004, 0.998, 1.002, 1.001],
                    early=[1.10, 0.95, 1.25, 1.00],
                    late=[1.00, 1.20, 0.90, 1.10],
                    permute=[1.001, 1.003, 0.999],
                )
            )
        )
        self.assertEqual(result.verdict, INCONCLUSIVE)
        self.assertGreater(result.primary_mde, result.margin)

    def test_scarred_negative_control_returns_design_failure(self):
        # A vocabulary permutation that does not recover means the deficit pair does not
        # isolate what it claims to isolate. No critical-period claim survives this.
        losses = grid(
            baseline=[1.000, 1.004, 0.998, 1.002, 1.001],
            early=[1.200, 1.210, 1.190, 1.205],
            late=[1.050, 1.060, 1.040, 1.055],
            permute=[1.300, 1.310, 1.290],
        )
        result = study_verdict(build_records(losses))
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("negative control" in reason for reason in result.reasons))

    def test_design_failure_outranks_a_positive_primary_result(self):
        # The control is checked before the primary contrast is read, so a planted effect
        # cannot rescue a broken design.
        losses = grid(
            baseline=[1.000, 1.004, 0.998, 1.002, 1.001],
            early=[1.500, 1.510, 1.490, 1.505],
            late=[1.050, 1.060, 1.040, 1.055],
            permute=[1.300, 1.310, 1.290],
        )
        self.assertEqual(study_verdict(build_records(losses)).verdict, DESIGN_FAILURE)


class MechanicalGateTests(unittest.TestCase):
    good = grid(
        baseline=[1.000, 1.004, 0.998, 1.002, 1.001],
        early=[1.200, 1.210, 1.190, 1.205],
        late=[1.050, 1.060, 1.040, 1.055],
        permute=[1.001, 1.003, 0.999],
    )

    def test_unequal_total_steps_is_a_design_failure(self):
        records = build_records(self.good)
        mismatched = [
            RunRecord(r.condition, r.seed, r.final_eval_loss, r.total_steps + 1)
            if r.condition == "shuffle_late_N4"
            else r
            for r in records
        ]
        result = study_verdict(mismatched)
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("total_steps" in reason for reason in result.reasons))

    def test_a_diverged_run_is_a_design_failure(self):
        records = build_records(self.good)
        records[0] = RunRecord("baseline", 0, math.nan, TOTAL_STEPS)
        result = study_verdict(records)
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("non-finite" in reason for reason in result.reasons))

    def test_a_missing_primary_condition_is_a_design_failure(self):
        losses = dict(self.good)
        del losses["shuffle_late_N4"]
        result = study_verdict(build_records(losses))
        self.assertEqual(result.verdict, DESIGN_FAILURE)

    def test_an_unresolvable_instrument_is_a_design_failure_not_a_null(self):
        # Baseline barely moved off random initialization, so the margin is a large
        # fraction of everything the model ever learned.
        result = study_verdict(
            build_records(
                grid(
                    baseline=[0.90, 1.10, 0.95, 1.05, 1.00],
                    early=[1.00, 1.02, 0.98, 1.01],
                    late=[1.00, 1.01, 0.99, 1.02],
                    permute=[1.00, 1.01, 0.99],
                )
            ),
            random_baseline_loss=1.50,
        )
        self.assertEqual(result.verdict, DESIGN_FAILURE)
        self.assertTrue(any("resolve" in reason for reason in result.reasons))


if __name__ == "__main__":
    unittest.main()

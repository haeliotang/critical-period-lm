"""Tests for the WSD schedule and trunk/leg geometry.

The design exists for one property — that a deficit can be moved in training time without
being moved in learning rate — so that property is tested directly rather than inferred from
the schedule's construction. The cost saving is tested too, because it is the other half of
the argument for choosing this design over the cosine sweep.
"""

import unittest

import mlx.core as mx

from critical_period_lm import wsd
from critical_period_lm.wsd_train import WSDRunConfig, training_batches_from
from critical_period_lm.train import TrainConfig, training_batches
import numpy as np


class GeometryTests(unittest.TestCase):
    def test_the_trunk_reaches_the_largest_rungs_branch_point(self):
        self.assertEqual(wsd.trunk_steps(), wsd.branch_step(max(wsd.RUNGS)))

    def test_each_leg_completes_its_own_rung(self):
        for rung in wsd.RUNGS:
            with self.subTest(rung=rung):
                self.assertEqual(wsd.branch_step(rung) + wsd.leg_steps(rung), rung)

    def test_branch_points_are_distinct(self):
        points = [wsd.branch_step(r) for r in wsd.RUNGS]
        self.assertEqual(len(set(points)), len(points))

    def test_the_shared_trunk_is_cheaper_than_separate_runs(self):
        saving = 1 - wsd.total_steps() / wsd.separate_steps()
        self.assertGreater(saving, 0.30)

    def test_every_branch_point_lies_inside_or_at_the_trunk(self):
        for rung in wsd.RUNGS:
            with self.subTest(rung=rung):
                self.assertLessEqual(wsd.branch_step(rung), wsd.trunk_steps())


class ConstantRateTests(unittest.TestCase):
    """The property the design exists for."""

    def setUp(self):
        self.schedule = wsd.trunk_schedule()

    def rate_at(self, step):
        return float(self.schedule(mx.array(step)))

    def test_the_stable_phase_holds_one_rate(self):
        start, stop = wsd.stable_phase()
        rates = {self.rate_at(s) for s in range(start, stop, 137)}
        self.assertEqual(len(rates), 1)

    def test_warmup_rises_from_zero_to_the_peak(self):
        self.assertEqual(self.rate_at(0), 0.0)
        self.assertAlmostEqual(self.rate_at(wsd.WARMUP_STEPS), wsd.WSDConfig().peak, places=9)

    def test_rate_matched_onsets_see_a_constant_rate_across_the_whole_deficit(self):
        for onset in wsd.ONSETS:
            if not wsd.is_rate_matched(onset):
                continue
            with self.subTest(onset=onset):
                span = {self.rate_at(onset + k) for k in range(0, wsd.DEFICIT_STEPS, 29)}
                self.assertEqual(len(span), 1)

    def test_onset_zero_is_correctly_flagged_as_unmatched(self):
        # It overlaps warmup, so its deficit spans a changing rate. Keeping it is a design
        # choice; letting it pass as rate-matched would not be.
        self.assertIn(0, wsd.UNMATCHED_ONSETS)
        self.assertFalse(wsd.is_rate_matched(0))
        self.assertNotEqual(self.rate_at(0), self.rate_at(wsd.DEFICIT_STEPS - 1))

    def test_five_of_the_six_candidate_onsets_are_matched(self):
        matched = [o for o in wsd.ONSETS if wsd.is_rate_matched(o)]
        self.assertEqual(len(matched), len(wsd.ONSETS) - len(wsd.UNMATCHED_ONSETS))

    def test_a_deficit_running_past_the_trunk_is_not_matched(self):
        self.assertFalse(wsd.is_rate_matched(wsd.trunk_steps() - 10))


class LegScheduleTests(unittest.TestCase):
    def test_each_leg_starts_at_the_peak_and_reaches_exactly_zero(self):
        for rung in wsd.RUNGS:
            with self.subTest(rung=rung):
                schedule = wsd.leg_schedule(rung)
                self.assertAlmostEqual(
                    float(schedule(mx.array(0))), wsd.WSDConfig().peak, places=9
                )
                self.assertAlmostEqual(
                    float(schedule(mx.array(wsd.leg_steps(rung)))), 0.0, places=12
                )

    def test_the_leg_is_monotonically_decreasing(self):
        schedule = wsd.leg_schedule(5_400)
        rates = [float(schedule(mx.array(s))) for s in range(0, wsd.leg_steps(5_400), 40)]
        self.assertEqual(rates, sorted(rates, reverse=True))


class BatchStreamTests(unittest.TestCase):
    def test_the_resumable_iterator_matches_the_trainers_own(self):
        # The leg must draw what the trunk would have drawn next. If this file's iterator
        # ever diverges from train.training_batches, the two designs stop being comparable.
        tokens = np.arange(50_000, dtype=np.int32)
        wsd_config = WSDRunConfig(seed=3)
        train_config = TrainConfig(seed=3, batch_size=wsd_config.batch_size)
        mine = training_batches_from(tokens, wsd_config, np.random.default_rng(3))
        theirs = training_batches(tokens, train_config)
        for _ in range(4):
            np.testing.assert_array_equal(next(mine), next(theirs))


class ConfigTests(unittest.TestCase):
    def test_the_deficit_window_uses_absolute_steps_not_budget_fractions(self):
        config = WSDRunConfig(deficit="shuffle", onset=600, duration=400)
        schedule = config.deficit_schedule()
        self.assertEqual((schedule.onset_step, schedule.duration_steps), (600, 400))

    def test_the_baseline_carries_no_deficit(self):
        self.assertEqual(WSDRunConfig().deficit_schedule().kind, "none")

    def test_the_fixed_control_gets_its_window_permutation(self):
        self.assertIsNotNone(WSDRunConfig(deficit="fixed").deficit_schedule().window_permutation)

    def test_a_baseline_counts_as_rate_matched(self):
        self.assertTrue(WSDRunConfig().rate_matched)


if __name__ == "__main__":
    unittest.main()

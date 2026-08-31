"""Rehearsal gate for the v6 verdict function.

A judgment rule that has never been run against a known answer is not a registered rule. v5's
`decision_rules.py` had to return each of its five verdicts correctly against fabricated
ladders before it was allowed to see a real run; this module owes the same debt and does not
inherit v5's payment, because the verdict logic is new even though every primitive under it
is not.

Each test plants a ground truth — an onset curve of a known shape, a control that does or does
not move, an arm that does or does not decay — and requires the frozen-to-be code to name it.
The planted data is built by `ladder()` from an explicit `gap(T) = c / T^alpha`, so the answer
is known by construction rather than by simulation.
"""

import unittest

from critical_period_lm.decision_rules import RunRecord
from critical_period_lm.wsd_decision import (
    ARM_DID_NOT_DECAY,
    CONTROL_ONSET_DEPENDENT,
    INCONCLUSIVE,
    NO_ONSET_EFFECT,
    ONSET_EFFECT,
    concordance_p,
    kendall_w,
    margin_from,
    onset_of,
    study_verdict,
)

BUDGETS = (1_350, 2_700, 5_400)
SEEDS = tuple(range(8))
MATCHED = {108, 600, 1_400, 2_600, 3_800}


def ladder(arms: dict[str, float], jitter: float = 0.0, amplitude: float = 40.0,
           jitters: dict[str, float] | None = None):
    """Records with a planted exponent per condition.

    `arms` maps a condition name to the exponent its gap should decay with. `jitter` spreads
    the per-seed exponents deterministically, which is what the margin is estimated from;
    `jitters` overrides it per condition, so a noisy control can be planted alongside clean
    arms. That combination is v4's failure mode and there is no way to reach it otherwise.
    """
    records = []
    for budget in BUDGETS:
        for seed in SEEDS:
            base = 2.0 + 0.001 * seed
            records.append(RunRecord("baseline", seed, base, budget))
            for condition, alpha in arms.items():
                width = (jitters or {}).get(condition, jitter)
                shift = width * ((seed % 4) - 1.5)
                gap = amplitude / budget ** (alpha + shift)
                records.append(RunRecord(condition, seed, base + gap, budget))
    return records


class HelperTests(unittest.TestCase):
    def test_the_onset_is_read_off_the_condition_name(self):
        self.assertEqual(onset_of("shuffle_2600"), 2_600)
        self.assertEqual(onset_of("fixed_108"), 108)

    def test_the_margin_is_three_times_the_controls_scatter(self):
        self.assertAlmostEqual(margin_from([1.0, 1.2, 1.4, 1.6]), 3 * 0.2582, places=3)

    def test_the_margin_never_falls_below_its_floor(self):
        self.assertAlmostEqual(margin_from([1.0, 1.0, 1.0, 1.0]), 0.10)

    def test_concordance_is_one_when_every_seed_agrees(self):
        self.assertAlmostEqual(kendall_w([[1, 2, 3, 4, 5]] * 8), 1.0)

    def test_concordance_is_zero_when_seeds_cancel(self):
        self.assertAlmostEqual(kendall_w([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]] * 4), 0.0)

    def test_agreement_is_significant_and_cancellation_is_not(self):
        self.assertLess(concordance_p([[1, 2, 3, 4, 5]] * 8), 0.01)
        self.assertGreater(concordance_p([[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]] * 4), 0.5)


class PlantedVerdictTests(unittest.TestCase):
    """Each of the verdicts, against a curve whose answer is known before the code runs."""

    def test_a_planted_onset_effect_is_named(self):
        result = study_verdict(
            ladder({"fixed_108": 1.15, "shuffle_108": 1.15, "shuffle_3800": 0.70}, jitter=0.01),
            MATCHED,
        )
        self.assertEqual(result.verdict, ONSET_EFFECT)
        self.assertAlmostEqual(result.primary_delta, 0.45, places=2)

    def test_a_planted_flat_curve_is_named_a_null(self):
        result = study_verdict(
            ladder(
                {"fixed_108": 1.15, "shuffle_108": 1.15, "shuffle_1400": 1.15,
                 "shuffle_3800": 1.15},
                jitter=0.02,
            ),
            MATCHED,
        )
        self.assertEqual(result.verdict, NO_ONSET_EFFECT)
        self.assertLess(abs(result.primary_delta), result.margin)

    def test_a_control_that_moves_with_onset_voids_the_axis(self):
        # The control is information-preserving, so its exponent must not depend on onset.
        # If it does, nothing downstream is interpretable and no primary is reported.
        result = study_verdict(
            ladder(
                {"fixed_108": 1.15, "fixed_3800": 0.60, "shuffle_108": 1.15,
                 "shuffle_3800": 0.70},
                jitter=0.01,
            ),
            MATCHED,
        )
        self.assertEqual(result.verdict, CONTROL_ONSET_DEPENDENT)
        self.assertIn("confounded", " ".join(result.reasons))

    def test_an_arm_that_does_not_decay_is_caught_before_the_primary(self):
        # A flat gap means the arm had no time to recover, which is not slow repair. This is
        # the most likely way the design fails and it is named rather than absorbed.
        result = study_verdict(
            ladder({"fixed_108": 1.15, "shuffle_108": 1.15, "shuffle_3800": 0.0},
                   jitter=0.005),
            MATCHED,
        )
        self.assertEqual(result.verdict, ARM_DID_NOT_DECAY)
        self.assertIn("shuffle_3800", " ".join(result.reasons))

    def test_an_effect_below_the_margin_but_significant_is_inconclusive(self):
        # v4's failure mode, transplanted: a cleanly separated difference that is nonetheless
        # smaller than the noise scale the design committed to respecting, because the control
        # happened to scatter. It must not be reported as a finding.
        result = study_verdict(
            ladder(
                {"fixed_108": 1.15, "shuffle_108": 1.15, "shuffle_3800": 1.05},
                jitters={"fixed_108": 0.15, "shuffle_108": 0.002, "shuffle_3800": 0.002},
            ),
            MATCHED,
        )
        self.assertLess(abs(result.primary_delta), result.margin)
        self.assertLessEqual(result.primary_p, 0.05)
        self.assertEqual(result.verdict, INCONCLUSIVE)


class BlindSpotTests(unittest.TestCase):
    """The reason concordance is registered alongside the pairwise contrast."""

    def test_a_dip_that_returns_is_not_reported_as_flat(self):
        # Extremes equal, middle lower -- exactly the shape Achille et al. report in vision.
        # The pairwise contrast cannot see it; the verdict must not therefore call it a null.
        result = study_verdict(
            ladder(
                {"fixed_108": 1.15, "shuffle_108": 1.15, "shuffle_600": 0.95,
                 "shuffle_1400": 0.80, "shuffle_2600": 0.95, "shuffle_3800": 1.15},
                jitter=0.004,
            ),
            MATCHED,
        )
        self.assertLess(abs(result.primary_delta), result.margin)
        self.assertNotEqual(result.verdict, NO_ONSET_EFFECT)
        self.assertEqual(result.verdict, INCONCLUSIVE)
        self.assertIn("non-monotonic", " ".join(result.reasons))

    def test_a_genuinely_flat_curve_still_reaches_the_null(self):
        # The guard must not fire on everything, or it would make a null unreachable.
        result = study_verdict(
            ladder(
                {"fixed_108": 1.15, "shuffle_108": 1.15, "shuffle_600": 1.15,
                 "shuffle_1400": 1.15, "shuffle_2600": 1.15, "shuffle_3800": 1.15},
                jitter=0.03,
            ),
            MATCHED,
        )
        self.assertEqual(result.verdict, NO_ONSET_EFFECT)


class ScopeTests(unittest.TestCase):
    def test_unmatched_onsets_are_excluded_from_the_primary(self):
        # Onset 0 overlaps warmup and is not learning-rate-matched. It is reported, and it
        # may not carry the contrast -- otherwise the design's whole point is given away.
        records = ladder(
            {"fixed_108": 1.15, "shuffle_0": 0.40, "shuffle_108": 1.15, "shuffle_3800": 1.14},
            jitter=0.02,
        )
        result = study_verdict(records, MATCHED)
        self.assertEqual(result.verdict, NO_ONSET_EFFECT)
        unmatched = [f for f in result.fits if f.condition == "shuffle_0"]
        self.assertEqual(len(unmatched), 1)
        self.assertFalse(unmatched[0].rate_matched)

    def test_every_condition_is_reported_whatever_the_verdict(self):
        result = study_verdict(
            ladder({"fixed_108": 1.15, "shuffle_108": 1.15, "shuffle_3800": 0.70},
                   jitter=0.01),
            MATCHED,
        )
        self.assertEqual({f.condition for f in result.fits},
                         {"fixed_108", "shuffle_108", "shuffle_3800"})

    def test_a_verdict_always_carries_a_reason(self):
        for arms in (
            {"fixed_108": 1.15, "shuffle_108": 1.15, "shuffle_3800": 0.70},
            {"fixed_108": 1.15, "shuffle_108": 1.15, "shuffle_3800": 1.15},
        ):
            with self.subTest(arms=sorted(arms)):
                self.assertTrue(study_verdict(ladder(arms, jitter=0.01), MATCHED).reasons)


if __name__ == "__main__":
    unittest.main()

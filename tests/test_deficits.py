"""Tests for the two registered deficits.

Each deficit has one property it must have for the design to mean anything: Deficit S must
destroy order while preserving token frequencies, and Deficit P must be losslessly
invertible. Those two properties are what license the interpretation in `CLAIMS.md`, so
they are asserted here rather than assumed.
"""

import unittest

import numpy as np

from critical_period_lm.deficits import (
    DEFICIT_FRACTIONS,
    FIXED,
    NONE,
    PERMUTE,
    RECOVERY_MULTIPLIER,
    SHUFFLE,
    SHUFFLE_WINDOW,
    TOTAL_BUDGET_MULTIPLE,
    WARMUP_FRACTION,
    DeficitSchedule,
    apply_vocab_permutation,
    clean_budget,
    fixed_window_shuffle,
    make_vocab_permutation,
    make_window_permutation,
    steps_from_clean_budget,
    warmup_steps,
    window_shuffle,
)


class WindowShuffleTests(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.default_rng(0)
        # Token id equals its position in the sequence, so a token that moved across a
        # window boundary is visible by value alone.
        self.tokens = np.tile(np.arange(64, dtype=np.int32), (4, 1))

    def test_shape_and_dtype_survive(self):
        out = window_shuffle(self.tokens, self.rng)
        self.assertEqual(out.shape, self.tokens.shape)
        self.assertEqual(out.dtype, self.tokens.dtype)

    def test_token_frequencies_are_preserved_within_every_window(self):
        out = window_shuffle(self.tokens, self.rng)
        for start in range(0, self.tokens.shape[-1], SHUFFLE_WINDOW):
            stop = start + SHUFFLE_WINDOW
            before = np.sort(self.tokens[:, start:stop], axis=-1)
            after = np.sort(out[:, start:stop], axis=-1)
            np.testing.assert_array_equal(before, after)

    def test_tokens_never_cross_a_window_boundary(self):
        out = window_shuffle(self.tokens, self.rng)
        for start in range(0, self.tokens.shape[-1], SHUFFLE_WINDOW):
            stop = start + SHUFFLE_WINDOW
            window = out[:, start:stop]
            self.assertTrue(((window >= start) & (window < stop)).all())

    def test_order_actually_changes(self):
        out = window_shuffle(self.tokens, self.rng)
        self.assertFalse(np.array_equal(out, self.tokens))

    def test_a_short_trailing_span_is_shuffled_too(self):
        # A sequence length that is not a multiple of the window must not leave a clean
        # tail, or part of every batch would escape the deficit.
        tokens = np.arange(2 * 20, dtype=np.int32).reshape(2, 20)
        rng = np.random.default_rng(1)
        changed = any(
            not np.array_equal(window_shuffle(tokens, rng)[:, 16:], tokens[:, 16:])
            for _ in range(20)
        )
        self.assertTrue(changed)

    def test_permutations_are_resampled_between_calls(self):
        first = window_shuffle(self.tokens, np.random.default_rng(0))
        second = window_shuffle(self.tokens, np.random.default_rng(1))
        self.assertFalse(np.array_equal(first, second))

    def test_a_degenerate_window_is_rejected(self):
        with self.assertRaises(ValueError):
            window_shuffle(self.tokens, self.rng, window=1)


class VocabPermutationTests(unittest.TestCase):
    def test_the_permutation_is_a_bijection(self):
        permutation = make_vocab_permutation(4096, seed=7)
        self.assertEqual(len(np.unique(permutation)), 4096)

    def test_relabeling_is_losslessly_invertible(self):
        # This is the property that makes Deficit P a statistics-preserving control: the
        # corrupted task is the clean task under a renaming, and nothing is destroyed.
        permutation = make_vocab_permutation(4096, seed=7)
        inverse = np.argsort(permutation)
        tokens = np.random.default_rng(3).integers(0, 4096, size=(4, 64))
        relabeled = apply_vocab_permutation(tokens, permutation)
        np.testing.assert_array_equal(inverse[relabeled], tokens)

    def test_the_same_seed_gives_the_same_permutation(self):
        np.testing.assert_array_equal(
            make_vocab_permutation(512, seed=7), make_vocab_permutation(512, seed=7)
        )


class FixedWindowShuffleTests(unittest.TestCase):
    """Deficit F, the negative control.

    Its whole job is to differ from Deficit S in exactly one respect — the permutation is
    fixed rather than resampled — so that a scar under S and recovery under F isolates the
    destruction of order information rather than the disturbance of the input.

    The previous control, a vocabulary permutation, failed this in pilot 2: at the same
    onset and duration it left twelve times the damage of Deficit S, because with tied
    embeddings it invalidates the input and output interface instead of perturbing input.
    """

    def setUp(self):
        self.permutation = make_window_permutation(seed=11)
        self.tokens = np.tile(np.arange(64, dtype=np.int32), (4, 1))

    def test_the_reordering_is_invertible(self):
        # This is the property that makes it a control: nothing is destroyed, so a model
        # can in principle learn to read the scrambled order.
        scrambled = fixed_window_shuffle(self.tokens, self.permutation)
        inverse = np.argsort(self.permutation)
        recovered = fixed_window_shuffle(scrambled, inverse)
        np.testing.assert_array_equal(recovered, self.tokens)

    def test_it_is_deterministic_where_deficit_s_is_not(self):
        first = fixed_window_shuffle(self.tokens, self.permutation)
        second = fixed_window_shuffle(self.tokens, self.permutation)
        np.testing.assert_array_equal(first, second)
        resampled_a = window_shuffle(self.tokens, np.random.default_rng(0))
        resampled_b = window_shuffle(self.tokens, np.random.default_rng(1))
        self.assertFalse(np.array_equal(resampled_a, resampled_b))

    def test_it_disturbs_the_order_as_much_as_deficit_s_does(self):
        # A control that barely moves anything would prove nothing by recovering.
        scrambled = fixed_window_shuffle(self.tokens, self.permutation)
        moved = (scrambled != self.tokens).mean()
        self.assertGreater(moved, 0.5)

    def test_token_frequencies_survive_within_every_window(self):
        out = fixed_window_shuffle(self.tokens, self.permutation)
        for start in range(0, self.tokens.shape[-1], SHUFFLE_WINDOW):
            stop = start + SHUFFLE_WINDOW
            np.testing.assert_array_equal(
                np.sort(self.tokens[:, start:stop], axis=-1),
                np.sort(out[:, start:stop], axis=-1),
            )

    def test_a_short_trailing_span_stays_a_bijection(self):
        tokens = np.tile(np.arange(20, dtype=np.int32), (2, 1))
        out = fixed_window_shuffle(tokens, self.permutation)
        np.testing.assert_array_equal(np.sort(out[:, 16:], axis=-1), np.sort(tokens[:, 16:], axis=-1))


class WarmupTests(unittest.TestCase):
    def test_warmup_is_the_same_fraction_at_every_budget(self):
        # Pilot 2 used a fixed 500 steps, which put 100% of the early deficit inside warmup
        # at pilot scale and 16% at full scale, so the two budgets ran different treatments.
        for total in (5_400, 21_600, 43_200):
            self.assertAlmostEqual(warmup_steps(total) / total, WARMUP_FRACTION, places=3)

    def test_warmup_is_a_minority_of_the_largest_deficit(self):
        for total in (5_400, 43_200):
            deficit = steps_from_clean_budget(total, max(DEFICIT_FRACTIONS))
            self.assertLess(warmup_steps(total) / deficit, 0.5)

    def test_warmup_is_never_zero(self):
        self.assertGreaterEqual(warmup_steps(10), 1)


class BudgetGeometryTests(unittest.TestCase):
    """The registered budget arithmetic, Sections 4.3 and 4.4.

    These live in the freeze corpus because pilot 1 was run at a geometry the design never
    specified: the fractions were applied to the run length instead of to the clean budget,
    which shrank the recovery allowance from 12.5:1 to 5.2:1 and doubled the asymmetry
    between the two arms. The constant that would have prevented it existed but was used
    nowhere.
    """

    def test_the_total_budget_multiple_is_the_registered_one(self):
        self.assertEqual(RECOVERY_MULTIPLIER, 2.0)
        self.assertEqual(max(DEFICIT_FRACTIONS), 0.16)
        self.assertAlmostEqual(TOTAL_BUDGET_MULTIPLE, 2.16)

    def test_the_clean_budget_inverts_the_total(self):
        self.assertAlmostEqual(clean_budget(43_200), 20_000)

    def test_the_largest_deficit_is_a_small_fraction_of_the_run(self):
        # 0.16 of T is 7.4% of T_total. If this ever reads 16%, the denominator is wrong.
        steps = steps_from_clean_budget(43_200, 0.16)
        self.assertEqual(steps, 3_200)
        self.assertAlmostEqual(steps / 43_200, 0.074, places=3)

    def test_recovery_dwarfs_the_largest_deficit(self):
        total = 43_200
        deficit = steps_from_clean_budget(total, max(DEFICIT_FRACTIONS))
        self.assertGreaterEqual((total - deficit) / deficit, 12.0)


class ScheduleTests(unittest.TestCase):
    def test_the_window_is_half_open(self):
        schedule = DeficitSchedule(kind=SHUFFLE, onset_step=100, duration_steps=50)
        self.assertFalse(schedule.active_at(99))
        self.assertTrue(schedule.active_at(100))
        self.assertTrue(schedule.active_at(149))
        self.assertFalse(schedule.active_at(150))

    def test_the_baseline_is_never_active(self):
        schedule = DeficitSchedule()
        self.assertEqual(schedule.kind, NONE)
        self.assertFalse(any(schedule.active_at(step) for step in range(0, 1000, 7)))

    def test_zero_duration_is_never_active(self):
        schedule = DeficitSchedule(kind=SHUFFLE, onset_step=0, duration_steps=0)
        self.assertFalse(schedule.active_at(0))

    def test_batches_outside_the_window_pass_through_untouched(self):
        tokens = np.arange(2 * 32, dtype=np.int32).reshape(2, 32)
        schedule = DeficitSchedule(kind=SHUFFLE, onset_step=10, duration_steps=5)
        rng = np.random.default_rng(0)
        np.testing.assert_array_equal(schedule.apply(tokens, 9, rng), tokens)
        np.testing.assert_array_equal(schedule.apply(tokens, 15, rng), tokens)
        self.assertFalse(np.array_equal(schedule.apply(tokens, 10, rng), tokens))

    def test_permute_deficit_requires_its_fixed_permutation(self):
        with self.assertRaises(ValueError):
            DeficitSchedule(kind=PERMUTE, onset_step=0, duration_steps=10)

    def test_the_fixed_control_requires_its_window_permutation(self):
        with self.assertRaises(ValueError):
            DeficitSchedule(kind=FIXED, onset_step=0, duration_steps=10)

    def test_an_unknown_deficit_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            DeficitSchedule(kind="blur", onset_step=0, duration_steps=10)


if __name__ == "__main__":
    unittest.main()

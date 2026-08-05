"""Tests for the two registered deficits.

Each deficit has one property it must have for the design to mean anything: Deficit S must
destroy order while preserving token frequencies, and Deficit P must be losslessly
invertible. Those two properties are what license the interpretation in `CLAIMS.md`, so
they are asserted here rather than assumed.
"""

import unittest

import numpy as np

from critical_period_lm.deficits import (
    NONE,
    PERMUTE,
    SHUFFLE,
    SHUFFLE_WINDOW,
    DeficitSchedule,
    apply_vocab_permutation,
    make_vocab_permutation,
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

    def test_an_unknown_deficit_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            DeficitSchedule(kind="blur", onset_step=0, duration_steps=10)


if __name__ == "__main__":
    unittest.main()

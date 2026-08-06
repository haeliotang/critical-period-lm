"""Tests for the trainer's guarantees.

Not part of the freeze corpus, but the properties checked here are what make the run
records mean what the design says they mean: conditions are paired by seed, evaluation is
identical everywhere, and the two gates refuse rather than warn.

None of these tests train a model. Both gates fire before any data is loaded, and the batch
machinery is pure numpy, so the suite stays fast enough to run on every change.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import numpy as np

from critical_period_lm import freeze, train as train_module
from critical_period_lm.deficits import PERMUTE, SHUFFLE
from critical_period_lm.model import ModelConfig
from critical_period_lm.train import (
    TrainConfig,
    evaluation_batches,
    training_batches,
)

SMALL_MODEL = ModelConfig(vocab_size=64, d_model=16, n_layers=1, n_heads=2, d_ff=32, seq_len=8)


def take(config: TrainConfig, tokens: np.ndarray, n: int) -> list[np.ndarray]:
    stream = training_batches(tokens, config)
    return [next(stream) for _ in range(n)]


class BatchStreamTests(unittest.TestCase):
    def setUp(self):
        self.tokens = np.arange(10_000, dtype=np.uint16) % 64

    def test_same_seed_gives_the_same_data_in_every_condition(self):
        # This is what makes the seed a paired unit. If the deficit condition also saw
        # different data, the contrast would carry two differences instead of one.
        baseline = TrainConfig(condition="baseline", seed=3, model=SMALL_MODEL)
        deficit = TrainConfig(
            condition="shuffle_early_N4",
            seed=3,
            deficit=SHUFFLE,
            duration_frac=0.16,
            model=SMALL_MODEL,
        )
        for left, right in zip(take(baseline, self.tokens, 5), take(deficit, self.tokens, 5)):
            np.testing.assert_array_equal(left, right)

    def test_different_seeds_give_different_data(self):
        first = take(TrainConfig(seed=0, model=SMALL_MODEL), self.tokens, 3)
        second = take(TrainConfig(seed=1, model=SMALL_MODEL), self.tokens, 3)
        self.assertFalse(any(np.array_equal(a, b) for a, b in zip(first, second)))

    def test_batches_have_one_extra_token_for_the_shifted_target(self):
        config = TrainConfig(batch_size=4, model=SMALL_MODEL)
        batch = take(config, self.tokens, 1)[0]
        self.assertEqual(batch.shape, (4, SMALL_MODEL.seq_len + 1))


class EvaluationTests(unittest.TestCase):
    tokens = np.arange(50_000, dtype=np.uint16) % 64

    def test_evaluation_windows_are_deterministic(self):
        config = TrainConfig(batch_size=4, eval_batches=3, model=SMALL_MODEL)
        np.testing.assert_array_equal(
            evaluation_batches(self.tokens, config), evaluation_batches(self.tokens, config)
        )

    def test_evaluation_windows_do_not_depend_on_the_seed_or_condition(self):
        first = evaluation_batches(
            self.tokens, TrainConfig(seed=0, batch_size=4, eval_batches=3, model=SMALL_MODEL)
        )
        second = evaluation_batches(
            self.tokens,
            TrainConfig(
                seed=9,
                condition="shuffle_late_N4",
                deficit=SHUFFLE,
                batch_size=4,
                eval_batches=3,
                model=SMALL_MODEL,
            ),
        )
        np.testing.assert_array_equal(first, second)

    def test_evaluation_windows_do_not_overlap(self):
        config = TrainConfig(batch_size=2, eval_batches=2, model=SMALL_MODEL)
        flat = evaluation_batches(self.tokens, config).reshape(-1, SMALL_MODEL.seq_len + 1)
        starts = [row[0] for row in flat]
        self.assertEqual(len(set(starts)), len(starts))


class ScheduleResolutionTests(unittest.TestCase):
    def test_fractions_resolve_against_the_clean_budget_not_the_run_length(self):
        # T_total = 43,200 means T = 20,000. A 0.16 fraction is 3,200 steps, which is 7.4%
        # of the run, not 16%. Pilot 1 was run at the wrong denominator and the recovery
        # allowance came out less than half of what the design specifies.
        config = TrainConfig(
            deficit=SHUFFLE, onset_frac=0.5, duration_frac=0.16, total_steps=43_200
        )
        schedule = config.schedule()
        self.assertEqual(schedule.onset_step, 10_000)
        self.assertEqual(schedule.duration_steps, 3_200)
        self.assertTrue(schedule.active_at(10_000))
        self.assertFalse(schedule.active_at(13_200))

    def test_the_two_arms_receive_equal_total_clean_training(self):
        # Matched on clean steps and on total steps; they differ only in where the deficit
        # sits, which is the whole point of the primary contrast.
        total = 43_200
        early = TrainConfig(
            deficit=SHUFFLE, onset_frac=0.0, duration_frac=0.16, total_steps=total
        ).schedule()
        late = TrainConfig(
            deficit=SHUFFLE, onset_frac=0.5, duration_frac=0.16, total_steps=total
        ).schedule()
        self.assertEqual(
            total - early.duration_steps, total - late.duration_steps
        )
        # But post-deficit recovery is not matched, and that asymmetry is a known
        # limitation rather than an accident. It runs against the registered direction.
        self.assertGreater(
            total - early.duration_steps, total - late.onset_step - late.duration_steps
        )

    def test_the_permute_deficit_gets_its_fixed_permutation(self):
        schedule = TrainConfig(
            deficit=PERMUTE, duration_frac=0.16, total_steps=1000, model=SMALL_MODEL
        ).schedule()
        self.assertIsNotNone(schedule.vocab_permutation)
        self.assertEqual(len(schedule.vocab_permutation), SMALL_MODEL.vocab_size)

    def test_the_baseline_never_applies_a_deficit(self):
        schedule = TrainConfig(total_steps=1000).schedule()
        self.assertFalse(any(schedule.active_at(s) for s in range(1000)))


class GateTests(unittest.TestCase):
    """Both gates must fire before any training happens, so neither costs an hour."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data_dir = Path(self._tmp.name) / "data"
        self.data_dir.mkdir()
        (self.data_dir / "manifest.json").write_text(json.dumps({"vocab_size": 64}))
        self.runs = Path(self._tmp.name) / "runs"
        patcher = patch.object(train_module, "RUNS_DIR", self.runs)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.config = TrainConfig(total_steps=1, model=SMALL_MODEL)

    def test_a_registered_run_refuses_without_an_intact_freeze(self):
        with patch.object(freeze, "verify_manifest", return_value=["design not frozen"]):
            with self.assertRaises(RuntimeError) as caught:
                train_module.train(self.config, self.data_dir, calibration=False)
        self.assertIn("intact freeze", str(caught.exception))

    def test_calibration_is_exempt_from_the_freeze_gate(self):
        # It must get past the gate; it then fails on the absent token arrays, which is a
        # different error and proves the gate was not what stopped it.
        with patch.object(freeze, "verify_manifest", return_value=["design not frozen"]):
            with self.assertRaises(FileNotFoundError):
                train_module.train(self.config, self.data_dir, calibration=True)

    def test_an_identical_config_refuses_to_overwrite_its_record(self):
        config_hash = self.config.config_hash({"vocab_size": 64})
        existing = self.runs / config_hash
        existing.mkdir(parents=True)
        (existing / "run.json").write_text("{}")

        with patch.object(freeze, "verify_manifest", return_value=[]):
            with self.assertRaises(FileExistsError):
                train_module.train(self.config, self.data_dir, calibration=False)

    def test_the_config_hash_separates_conditions_and_seeds(self):
        manifest = {"vocab_size": 64}
        base = TrainConfig(condition="baseline", seed=0, model=SMALL_MODEL)
        hashes = {
            base.config_hash(manifest),
            TrainConfig(condition="baseline", seed=1, model=SMALL_MODEL).config_hash(manifest),
            TrainConfig(
                condition="shuffle_early_N4", seed=0, deficit=SHUFFLE, model=SMALL_MODEL
            ).config_hash(manifest),
        }
        self.assertEqual(len(hashes), 3)

    def test_the_config_hash_tracks_the_corpus(self):
        base = TrainConfig(model=SMALL_MODEL)
        self.assertNotEqual(
            base.config_hash({"train_sha256": "aaa"}), base.config_hash({"train_sha256": "bbb"})
        )


if __name__ == "__main__":
    unittest.main()

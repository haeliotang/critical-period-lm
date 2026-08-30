"""Tests for complete-training-state checkpointing.

The trunk-branch design fails silently if a checkpoint omits one component: the leg trains
perfectly well and measures something else. So each of the five components is checked
individually, and a checkpoint missing any of them is required to raise rather than restore a
plausible-looking partial state.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
import numpy as np
from mlx.utils import tree_flatten

from critical_period_lm.checkpoint import FORMAT_VERSION, Streams, load_meta, restore, save
from critical_period_lm.model import ModelConfig, Transformer

TINY = ModelConfig(vocab_size=64, d_model=32, n_layers=2, n_heads=4, d_ff=64, seq_len=16)


def _built(seed=0):
    mx.random.seed(seed)
    model = Transformer(TINY)
    mx.eval(model.parameters())
    optimizer = optim.AdamW(learning_rate=1e-3)
    return model, optimizer


def _advance(model, optimizer, steps=3):
    """Take real steps so the optimizer moments and step counter are non-trivial."""
    def loss_fn(m, x, y):
        return m.loss(x, y)

    value_and_grad = nn.value_and_grad(model, loss_fn)
    rng = np.random.default_rng(0)
    for _ in range(steps):
        batch = mx.array(rng.integers(0, TINY.vocab_size, size=(2, TINY.seq_len + 1)))
        _, grads = value_and_grad(model, batch[:, :-1], batch[:, 1:])
        optimizer.update(model, grads)
        mx.eval(model.parameters(), optimizer.state)


class RoundTripTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "ckpt"
        self.addCleanup(shutil.rmtree, self.dir)

        self.model, self.optimizer = _built()
        _advance(self.model, self.optimizer)
        self.streams = Streams.for_seed(7)
        self.streams.data.integers(0, 100, size=5)
        self.streams.deficit.integers(0, 100, size=3)
        save(self.path, self.model, self.optimizer, self.streams)

    def _restored(self):
        model, optimizer = _built(seed=999)  # deliberately a different init
        streams = Streams.for_seed(0)  # and deliberately the wrong seed
        restore(self.path, model, optimizer, streams)
        return model, optimizer, streams

    def test_model_parameters_round_trip_exactly(self):
        model, _, _ = self._restored()
        for (name, before), (_, after) in zip(
            tree_flatten(self.model.parameters()), tree_flatten(model.parameters())
        ):
            with self.subTest(parameter=name):
                self.assertTrue(mx.array_equal(before, after).item())

    def test_optimizer_moments_and_step_round_trip(self):
        _, optimizer, _ = self._restored()
        before, after = dict(tree_flatten(self.optimizer.state)), dict(
            tree_flatten(optimizer.state)
        )
        self.assertEqual(set(before), set(after))
        for key in before:
            with self.subTest(key=key):
                self.assertTrue(mx.array_equal(before[key], after[key]).item())

    def test_the_optimizer_step_counter_survives(self):
        # Losing it restarts bias correction and the schedule, which is the subtlest way a
        # leg can look healthy and be wrong.
        _, optimizer, _ = self._restored()
        self.assertEqual(optimizer.state["step"].item(), 3)

    def test_mx_random_state_round_trips(self):
        before = [mx.array(part) for part in mx.random.state]
        self._restored()
        for i, part in enumerate(mx.random.state):
            with self.subTest(part=i):
                self.assertTrue(mx.array_equal(before[i], part).item())

    def test_both_numpy_streams_resume_where_they_stopped(self):
        expected_data = self.streams.data.integers(0, 100, size=4)
        expected_deficit = self.streams.deficit.integers(0, 100, size=4)
        _, _, streams = self._restored()
        np.testing.assert_array_equal(streams.data.integers(0, 100, size=4), expected_data)
        np.testing.assert_array_equal(
            streams.deficit.integers(0, 100, size=4), expected_deficit
        )

    def test_the_two_streams_are_not_the_same_generator(self):
        # Streams.for_seed offsets the deficit stream by one. If they collided, a deficit
        # would consume draws the data stream needs and the pairing across conditions would
        # quietly break.
        streams = Streams.for_seed(5)
        self.assertFalse(
            np.array_equal(
                streams.data.integers(0, 10**6, size=8),
                streams.deficit.integers(0, 10**6, size=8),
            )
        )


class RefusalTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "ckpt"
        self.addCleanup(shutil.rmtree, self.dir)
        model, optimizer = _built()
        _advance(model, optimizer)
        save(self.path, model, optimizer, Streams.for_seed(1))

    def test_a_checkpoint_missing_a_component_is_refused(self):
        arrays = dict(mx.load(str(self.path.with_suffix(".npz"))))
        for prefix, name in (("opt.", "optimizer"), ("mxrandom.", "mx.random")):
            with self.subTest(missing=name):
                kept = {k: v for k, v in arrays.items() if not k.startswith(prefix)}
                mx.savez(str(self.path.with_suffix(".npz")), **kept)
                model, optimizer = _built()
                with self.assertRaises(ValueError) as caught:
                    restore(self.path, model, optimizer, Streams.for_seed(1))
                self.assertIn(name, str(caught.exception))
                mx.savez(str(self.path.with_suffix(".npz")), **arrays)

    def test_a_foreign_format_version_is_refused(self):
        import json

        payload = json.loads(self.path.with_suffix(".json").read_text())
        payload["format_version"] = FORMAT_VERSION + 1
        self.path.with_suffix(".json").write_text(json.dumps(payload))
        with self.assertRaises(ValueError):
            load_meta(self.path)


if __name__ == "__main__":
    unittest.main()

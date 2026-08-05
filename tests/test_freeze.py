"""Tests for the freeze mechanism.

The point of the freeze is that a change to a design-defining file is detected rather than
noticed. These tests check that detection actually happens, using a temporary copy of the
repository so that nothing here can touch the real manifest.
"""

import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from critical_period_lm import freeze


class ManifestTests(unittest.TestCase):
    def test_every_bound_file_exists(self):
        for name in freeze.BOUND_FILES:
            self.assertTrue((freeze.ROOT / name).is_file(), f"missing bound file: {name}")

    def test_the_judgment_code_and_the_deficits_are_bound(self):
        # If these two drift after freeze, the study's verdicts and its manipulation are
        # no longer the ones that were registered.
        self.assertIn("src/critical_period_lm/decision_rules.py", freeze.BOUND_FILES)
        self.assertIn("src/critical_period_lm/deficits.py", freeze.BOUND_FILES)

    def test_manifest_is_stable_across_builds(self):
        self.assertEqual(freeze.build_manifest(), freeze.build_manifest())


def copy_bound_files_to(root: Path) -> None:
    for name in freeze.BOUND_FILES:
        destination = root / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(freeze.ROOT / name, destination)


class TamperDetectionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.manifest = self.root / "freeze-manifest.json"
        copy_bound_files_to(self.root)

        patcher_root = patch.object(freeze, "ROOT", self.root)
        patcher_manifest = patch.object(freeze, "MANIFEST_PATH", self.manifest)
        patcher_root.start()
        patcher_manifest.start()
        self.addCleanup(patcher_root.stop)
        self.addCleanup(patcher_manifest.stop)

    def test_an_edited_bound_file_is_a_freeze_violation(self):
        self.manifest.write_text(json.dumps(freeze.build_manifest(), indent=2))
        self.assertEqual(freeze.verify_manifest(), [])

        target = self.root / "src/critical_period_lm/decision_rules.py"
        target.write_text(target.read_text().replace("ALPHA = 0.05", "ALPHA = 0.10"))

        problems = freeze.verify_manifest()
        self.assertTrue(
            any("decision_rules.py changed after freeze" in p for p in problems), problems
        )

    def test_a_missing_manifest_is_reported_as_not_frozen(self):
        problems = freeze.verify_manifest()
        self.assertTrue(any("not frozen" in p for p in problems), problems)

    def test_a_missing_bound_file_is_an_error_not_a_silent_pass(self):
        (self.root / "CLAIMS.md").unlink()
        with self.assertRaises(FileNotFoundError):
            freeze.build_manifest()

    def test_building_over_an_existing_manifest_is_refused(self):
        self.manifest.write_text(json.dumps(freeze.build_manifest(), indent=2))
        self.assertEqual(freeze.main(["freeze", "build"]), 1)


if __name__ == "__main__":
    unittest.main()

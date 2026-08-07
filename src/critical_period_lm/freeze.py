"""Freeze the design-defining files so that later runs cannot silently change them.

The freeze corpus is the set of files that decide what this study means: the registered
design, the claim register, the deficit definitions, and the judgment code. Everything
else — trainers, plotting, notes — is free to change while runs are in flight.

Usage:

    python -m critical_period_lm.freeze build    # write freeze-manifest.json
    python -m critical_period_lm.freeze verify   # fail if any bound file changed

The manifest is not the freeze on its own. The freeze is the annotated git tag that
contains it; the manifest just makes tampering mechanically detectable instead of
something a reader has to take on trust.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "freeze-manifest.json"

DESIGN_VERSION = "v2-draft"
FREEZE_TAG = "cplm-design-v1-frozen"

BOUND_FILES = (
    "preregistration.md",
    "CLAIMS.md",
    "src/critical_period_lm/decision_rules.py",
    "src/critical_period_lm/deficits.py",
    "tests/test_decision_rules.py",
    "tests/test_deficits.py",
)


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest() -> dict:
    missing = [name for name in BOUND_FILES if not (ROOT / name).is_file()]
    if missing:
        raise FileNotFoundError(f"bound file(s) missing: {', '.join(missing)}")

    files = [
        {"path": name, "sha256": file_digest(ROOT / name)} for name in sorted(BOUND_FILES)
    ]
    payload = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
    return {
        "design_version": DESIGN_VERSION,
        "freeze_tag": FREEZE_TAG,
        "files": files,
        "corpus_sha256": hashlib.sha256(payload).hexdigest(),
    }


def verify_manifest() -> list[str]:
    """Return the list of discrepancies. An empty list means the freeze holds."""
    if not MANIFEST_PATH.is_file():
        return [f"{MANIFEST_PATH.name} does not exist; the design is not frozen"]

    recorded = json.loads(MANIFEST_PATH.read_text())
    current = build_manifest()

    problems = []
    if recorded.get("design_version") != current["design_version"]:
        problems.append(
            f"design version drifted: manifest says {recorded.get('design_version')!r}, "
            f"code says {current['design_version']!r}"
        )

    recorded_files = {entry["path"]: entry["sha256"] for entry in recorded.get("files", [])}
    current_files = {entry["path"]: entry["sha256"] for entry in current["files"]}

    for path in sorted(set(recorded_files) | set(current_files)):
        if path not in recorded_files:
            problems.append(f"{path} is bound by the code but absent from the manifest")
        elif path not in current_files:
            problems.append(f"{path} is in the manifest but no longer bound")
        elif recorded_files[path] != current_files[path]:
            problems.append(f"{path} changed after freeze")

    return problems


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "verify"

    if command == "build":
        if MANIFEST_PATH.exists():
            print(
                f"{MANIFEST_PATH.name} already exists. Rebuilding it is a new design "
                "version, not an edit: delete it deliberately if that is what you mean.",
                file=sys.stderr,
            )
            return 1
        MANIFEST_PATH.write_text(json.dumps(build_manifest(), indent=2) + "\n")
        print(f"wrote {MANIFEST_PATH.name} for design {DESIGN_VERSION}")
        return 0

    if command == "verify":
        problems = verify_manifest()
        for problem in problems:
            print(f"FREEZE VIOLATION: {problem}", file=sys.stderr)
        if problems:
            return 1
        print(f"freeze intact: {len(BOUND_FILES)} bound files match {MANIFEST_PATH.name}")
        return 0

    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

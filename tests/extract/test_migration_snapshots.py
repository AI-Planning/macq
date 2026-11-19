"""Checks that extractors learn the same domain models while `macq.trace` moves onto `macq.core`. Temporary."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SNAPSHOTS = Path(__file__).parent / "migration_snapshots"
ROOT = Path(__file__).parent.parent.parent
SCENARIOS = sorted(path.stem for path in (SNAPSHOTS / "expected").glob("*.json"))


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_extractor_learns_the_snapshotted_model(scenario, tmp_path):
    output = tmp_path / "learned.json"
    env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONPATH": str(ROOT)}
    subprocess.run(
        [sys.executable, str(SNAPSHOTS / "harness.py"), "replay", scenario, str(output)],
        check=True,
        env=env,
        capture_output=True,
    )
    expected = json.loads((SNAPSHOTS / "expected" / f"{scenario}.json").read_text())
    assert json.loads(output.read_text()) == expected

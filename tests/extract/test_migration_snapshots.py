"""Checks that extractors learn the same content while they move onto `macq.core`. Temporary."""

import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

SNAPSHOTS = Path(__file__).parent / "migration_snapshots"
ROOT = Path(__file__).parent.parent.parent
SCENARIOS = sorted(path.stem for path in (SNAPSHOTS / "expected").glob("*.json"))


def _sorted(values):
    return sorted({json.dumps(v, sort_keys=True): v for v in values}.values(), key=lambda v: json.dumps(v, sort_keys=True))


def _with_locm_forced_fixes(expected):
    """Applies the only changes LOCM's output may have: arity suffixes, the zero object, and statics."""
    arities = defaultdict(set)
    for name, sorts, _ in expected["fluents"]:
        arities[name].add(len(sorts))

    actions = {}
    for signature, parts in expected["actions"].items():
        last_param = len(signature.split()) - 2

        def fixed(fluent):
            name, sorts, indices = fluent
            name = f"{name}_{len(sorts)}" if len(arities[name]) > 1 else name
            return [name, sorts, [last_param if i == -1 else i for i in indices]]

        actions[signature] = {
            part: [fixed(fluent) for fluent in fluents if isinstance(fluent, list)]
            for part, fluents in parts.items()
        }
        if {"next", "1", "2"} <= {f for f in parts["precond"] if isinstance(f, str)}:
            actions[signature]["precond"].append(["next", ["sort2", "sort1"], [1, 0]])
        actions[signature] = {part: _sorted(fluents) for part, fluents in actions[signature].items()}

    used = [fluent for parts in actions.values() for fluents in parts.values() for fluent in fluents]
    return {"fluents": _sorted(used), "actions": actions}


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_extractor_learns_the_snapshotted_content(scenario, tmp_path):
    output = tmp_path / "learned.json"
    env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONPATH": str(ROOT)}
    subprocess.run(
        [sys.executable, str(SNAPSHOTS / "harness.py"), "replay", scenario, str(output)],
        check=True,
        env=env,
        capture_output=True,
    )
    expected = json.loads((SNAPSHOTS / "expected" / f"{scenario}.json").read_text())
    if scenario.startswith("locm"):
        expected = _with_locm_forced_fixes(expected)
    assert json.loads(output.read_text()) == expected

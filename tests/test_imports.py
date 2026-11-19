"""Every public package imports on its own, whatever was imported before it."""
import subprocess
import sys

import pytest

PACKAGES = [
    "macq",
    "macq.core",
    "macq.trace",
    "macq.observation",
    "macq.io",
    "macq.extract",
    "macq.generate",
    "macq.generate.pddl",
]


@pytest.mark.parametrize("package", PACKAGES)
def test_package_imports_in_a_fresh_process(package):
    result = subprocess.run([sys.executable, "-c", f"import {package}"], capture_output=True)
    assert result.returncode == 0, result.stderr.decode()


def test_trace_exports_the_disordered_parallel_lists():
    code = (
        "import macq.observation\n"
        "from macq.trace import *\n"
        "assert DisorderedParallelActionsObservationLists.__name__\n"
        "assert ActionPair.__name__\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True)
    assert result.returncode == 0, result.stderr.decode()

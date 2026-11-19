import subprocess
import sys

import pytest

from macq.generate.pddl import Generator

IMPORT_WITH_NETWORK_BLOCKED = """
import socket
import sys

attempts = []


def blocked(*args, **kwargs):
    attempts.append(args)
    raise OSError("network blocked")


socket.getaddrinfo = blocked
socket.socket.connect = blocked

import macq.generate.pddl

assert not attempts, f"network attempts on import: {attempts}"
assert "macq.generate.pddl.planning_domains_api" not in sys.modules
"""


def test_import_stays_off_the_network_and_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", IMPORT_WITH_NETWORK_BLOCKED],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_problem_ids_still_reach_the_planning_domains_api(monkeypatch):
    from macq.generate.pddl import planning_domains_api

    class Reached(Exception):
        pass

    def get_problem(problem_id, formalism):
        raise Reached(problem_id)

    monkeypatch.setattr(planning_domains_api, "get_problem", get_problem)
    with pytest.raises(Reached):
        Generator(problem_id=212)

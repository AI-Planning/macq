import os
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from pddl import parse_domain, parse_problem
from pddl.parser.problem import ProblemParser

from macq.core import ObjectType, PlanningObject
from macq.trace import Trace
from macq.generate.pddl import UniformWalkSampling, trace_rng
from macq.utils import InvalidNumberOfTraces, InvalidPlanLength

HERE = Path(__file__).resolve().parent
FILES = HERE.parent.parent / "pddl_testing_files"
DOMAIN = FILES / "walk_domain.pddl"
PROBLEM = FILES / "walk_problem.pddl"
WRITE = HERE / "write_walks.py"
EXPECTED = HERE / "expected_uniform_walks"


def sampler(seed=1, max_actions=6, dom=DOMAIN, prob=PROBLEM):
    return UniformWalkSampling(dom, prob, seed=seed, max_actions=max_actions)


def actions(trace):
    return [step.action for step in trace if step.action is not None]


def test_a_full_walk_has_n_actions_and_n_plus_one_states():
    walks = [sampler(max_actions=3).generate_trace(i) for i in range(40)]
    full = [t for t in walks if len(actions(t)) == 3]
    assert full
    for trace in full:
        assert len(trace) == 4
        assert trace[-1].action is None
        assert [step.index for step in trace] == [1, 2, 3, 4]


def test_a_walk_that_reaches_a_dead_end_stops_and_is_kept():
    walker = sampler(max_actions=30)
    walks = [walker.generate_trace(i) for i in range(40)]
    short = [t for t in walks if len(actions(t)) < 30]
    assert short
    for trace in short:
        assert trace[-1].action is None
        assert len(trace) == len(actions(trace)) + 1
        last_action = actions(trace)[-1]
        assert (last_action.name, last_action.objects[1].name) == ("Move", "Pit")


def test_a_dead_initial_state_gives_one_state_and_no_actions():
    text = PROBLEM.read_text().replace("(At Hall)", "(At Pit)")
    text = text.replace("(KeyIn K1 Hall)", "").replace("(KeyIn k2 attic)", "")
    trace = sampler(prob=ProblemParser()(text)).generate_trace(0)
    assert len(trace) == 1
    assert trace[0].action is None


def test_walks_continue_past_the_goal():
    walker = sampler(max_actions=30)
    goal_passed = 0
    for i in range(40):
        for step in walker.generate_trace(i):
            holding = [f for f in step.state if f.name == "Holding" and step.state[f]]
            if any(f.objects[0].name == "K1" for f in holding) and step.action:
                goal_passed += 1
    assert goal_passed


def test_states_cover_every_ground_atom_including_static_ones():
    walker = sampler()
    trace = walker.generate_trace(0)
    expected = len(walker.task.ground_atoms())
    assert expected == len(walker.grounded_fluents)
    for step in trace:
        assert len(step.state) == expected
    names = {f.name for f in trace[0].state}
    assert names == {"At", "Linked", "KeyIn", "Holding"}


def test_names_keep_their_case():
    trace = sampler().generate_trace(0)
    objects = {o.name for f in trace[0].state for o in f.objects}
    assert {"Hall", "attic", "Pit", "K1", "k2"} == objects


def test_objects_carry_the_domain_type_hierarchy():
    walk = sampler(dom=FILES / "deliver_domain.pddl", prob=FILES / "deliver_problem.pddl").generate_trace(0)
    locatable = ObjectType("locatable")
    objects = {o.name: o for fluent in walk[0].state for o in fluent.objects}
    assert objects["t1"] == PlanningObject("t1", ObjectType("truck", ObjectType("vehicle", locatable)))
    assert objects["p1"] == PlanningObject("p1", ObjectType("package", locatable))
    assert objects["l1"] == PlanningObject("l1", ObjectType("location"))


def test_trace_actions_carry_no_preconditions_or_effects():
    for action in actions(sampler().generate_trace(0)):
        assert not action.positive_preconditions and not action.negative_preconditions
        assert not action.add_effects and not action.delete_effects
        assert action.cost is None


def test_each_applicable_action_is_picked_about_equally_often():
    walker = sampler(max_actions=1)
    first = Counter(
        " ".join([a.name, *[o.name for o in a.objects]])
        for i in range(3000)
        for a in actions(walker.generate_trace(i))
    )
    assert set(first) == {"Grab K1 Hall", "Move Hall attic", "Move Hall Pit"}
    assert all(800 < count < 1200 for count in first.values())


def test_a_trace_depends_only_on_its_index():
    walker = sampler()
    expected = walker.generate_trace(5)
    for i in range(4):
        walker.generate_trace(i)
    assert walker.generate_trace(5) == expected
    assert sampler().generate_trace(5) == expected


def test_iter_traces_matches_generate_trace():
    walker = sampler()
    walks = walker.iter_traces(3, start=2)
    assert not isinstance(walks, (list, tuple))
    generated = [trace for trace in walks]
    assert generated == [walker.generate_trace(i) for i in (2, 3, 4)]
    assert all(isinstance(t, Trace) for t in walker.iter_traces(1))


def test_parsed_objects_give_the_same_walks_as_paths():
    parsed = sampler(dom=parse_domain(DOMAIN), prob=parse_problem(PROBLEM))
    assert parsed.generate_trace(3) == sampler().generate_trace(3)


def test_the_sampler_does_not_change_the_global_generator():
    random.seed(9)
    before = random.getstate()
    sampler().generate_trace(0)
    assert random.getstate() == before


@pytest.mark.parametrize(
    "changed",
    [
        (2, "WalkTest", "WalkProblem", "walk", 0),
        (1, "Other", "WalkProblem", "walk", 0),
        (1, "WalkTest", "Other", "walk", 0),
        (1, "WalkTest", "WalkProblem", "noisy", 0),
        (1, "WalkTest", "WalkProblem", "walk", 1),
    ],
)
def test_every_seed_input_changes_the_generator(changed):
    base = trace_rng(1, "WalkTest", "WalkProblem", "walk", 0).random()
    assert trace_rng(*changed).random() != base


def test_seed_inputs_can_not_run_together():
    first = trace_rng(1, "ab", "c", "walk", 0).random()
    assert trace_rng(1, "a", "bc", "walk", 0).random() != first


def test_the_sampler_seeds_from_the_declared_names():
    expected = trace_rng(4, "WalkTest", "WalkProblem", "partial", 2).random()
    assert sampler(seed=4).trace_rng(2, "partial").random() == expected


def test_unknown_streams_are_rejected():
    with pytest.raises(ValueError):
        trace_rng(1, "d", "p", "wallk", 0)


@pytest.mark.parametrize("index", [-1, 1.5, True])
def test_invalid_indices_are_rejected(index):
    with pytest.raises(ValueError):
        sampler().generate_trace(index)


@pytest.mark.parametrize("seed", [None, 1.5, "1", True])
def test_the_seed_must_be_an_integer(seed):
    with pytest.raises(TypeError):
        sampler(seed=seed)


def test_the_seed_is_required():
    with pytest.raises(TypeError):
        UniformWalkSampling(DOMAIN, PROBLEM, max_actions=3)


def test_problem_ids_are_not_accepted():
    with pytest.raises(TypeError):
        UniformWalkSampling(problem_id=212, seed=1, max_actions=3)


@pytest.mark.parametrize("max_actions", [0, -1])
def test_max_actions_must_be_positive(max_actions):
    with pytest.raises(InvalidPlanLength):
        sampler(max_actions=max_actions)


def test_a_negative_trace_count_is_rejected():
    with pytest.raises(InvalidNumberOfTraces):
        sampler().iter_traces(-1)


def run_python(*args, **env):
    root = str(HERE.parent.parent.parent)
    path = os.pathsep.join(filter(None, [root, os.environ.get("PYTHONPATH")]))
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        env={**os.environ, "PYTHONPATH": path, **env},
    )


WALK_WITH_NETWORK_BLOCKED = f"""
import socket
import sys

attempts = []


def blocked(*args, **kwargs):
    attempts.append(args)
    raise OSError("network blocked")


socket.getaddrinfo = blocked
socket.socket.connect = blocked

sys.path.insert(0, {str(HERE)!r})
from write_walks import write_all
import tempfile

with tempfile.TemporaryDirectory() as directory:
    write_all(directory)
assert not attempts, f"network attempts: {{attempts}}"
"""


def test_walks_and_observations_never_touch_the_network():
    # A separate process, because timed-out samplers in other tests can leave threads running.
    result = run_python("-c", WALK_WITH_NETWORK_BLOCKED)
    assert result.returncode == 0, result.stderr.decode()


@pytest.mark.parametrize("hash_seed", ["0", "1", "4242"])
def test_output_is_byte_identical_to_the_stored_walks(hash_seed, tmp_path):
    result = run_python(str(WRITE), str(tmp_path), PYTHONHASHSEED=hash_seed)
    assert result.returncode == 0, result.stderr.decode()
    expected = sorted(p.name for p in EXPECTED.iterdir())
    assert sorted(p.name for p in tmp_path.iterdir()) == expected
    assert len(expected) == 18
    for name in expected:
        assert (tmp_path / name).read_bytes() == (EXPECTED / name).read_bytes(), name

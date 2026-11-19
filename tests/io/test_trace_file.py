"""Tests for reading and writing trace files."""
import json
import random
from pathlib import Path

import pytest
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser

from macq.core import GroundedFluent, ObjectType, PlanningObject
from macq.generate.pddl import UniformWalkSampling, VanillaSampling
from macq.io import InvalidTraceFile, read_trace, read_traces, write_trace
from macq.observation import (
    ActionObservation,
    AtomicPartialObservation,
    IdentityObservation,
    NoisyObservation,
    PartialObservation,
)
from macq.trace import (
    PartialState,
    State,
    Step,
    Trace,
    TraceList,
)

DOMAIN_TEXT = """
(define (domain Trucks)
  (:requirements :strips :typing)
  (:types vehicle location - object Truck - vehicle)
  (:constants depot - location)
  (:predicates (at ?v - vehicle ?l - location) (road ?a ?b - location) (ready))
  (:action drive
    :parameters (?t - Truck ?from ?to - location)
    :precondition (and (at ?t ?from) (road ?from ?to))
    :effect (and (at ?t ?to) (not (at ?t ?from)) (ready))))
"""

PROBLEM_TEXT = """
(define (problem p) (:domain Trucks)
  (:objects t1 - Truck L1 L2 - location)
  (:init (at t1 L1) (road L1 L2) (road L2 L1) (road depot L1) (road L2 depot))
  (:goal (at t1 L2)))
"""

SHELL_TEXT = """
(define (domain Trucks)
  (:requirements :strips :typing)
  (:types vehicle location - object Truck - vehicle)
  (:constants depot L1 L2 - location t1 - Truck)
  (:predicates (at ?v - vehicle ?l - location) (road ?a ?b - location) (ready))
  (:action drive :parameters (?t - Truck ?from ?to - location)))
"""

ACTION_ONLY_SHELL_TEXT = """
(define (domain Trucks)
  (:requirements :strips :typing)
  (:types vehicle location - object Truck - vehicle)
  (:constants depot L1 L2 - location t1 - Truck)
  (:action drive :parameters (?t - Truck ?from ?to - location)))
"""


@pytest.fixture
def domain():
    return DomainParser()(DOMAIN_TEXT)


@pytest.fixture
def problem():
    return ProblemParser()(PROBLEM_TEXT)


@pytest.fixture
def shell():
    return DomainParser()(SHELL_TEXT)


def walk(domain, problem, index=0, max_actions=4):
    return UniformWalkSampling(domain, problem, seed=5, max_actions=max_actions).generate_trace(index)


def state_values(trace):
    return [{str(f): s.state[f] for f in s.state} for s in trace]


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


# -- round trips -------------------------------------------------------------


def test_trace_round_trips_with_a_problem(tmp_path, domain, problem):
    trace = walk(domain, problem)
    write_trace(tmp_path / "t.json", trace)
    assert read_trace(tmp_path / "t.json", domain, problem) == trace


def test_trace_round_trips_with_constants_only(tmp_path, domain, problem, shell):
    trace = walk(domain, problem)
    write_trace(tmp_path / "t.json", trace)
    read = read_trace(tmp_path / "t.json", shell)
    assert [s.action for s in read] == [s.action for s in trace]
    for original, back in zip(trace, read):
        for fluent, value in back.state.items():
            assert value == original.state.fluents.get(fluent, False)


def test_reader_accepts_paths(tmp_path, domain, problem):
    (tmp_path / "d.pddl").write_text(DOMAIN_TEXT)
    (tmp_path / "p.pddl").write_text(PROBLEM_TEXT)
    trace = walk(domain, problem)
    write_trace(tmp_path / "t.json", trace)
    read = read_trace(tmp_path / "t.json", tmp_path / "d.pddl", str(tmp_path / "p.pddl"))
    assert read == trace


def test_read_objects_keep_their_types(tmp_path, domain, problem):
    trace = walk(domain, problem)
    write_trace(tmp_path / "t.json", trace)
    read = read_trace(tmp_path / "t.json", domain, problem)
    types = {o.name: o.obj_type.type_name for f in read[0].state for o in f.objects}
    assert types == {"t1": "Truck", "L1": "location", "L2": "location", "depot": "location"}


def test_read_objects_carry_the_domain_type_hierarchy(tmp_path):
    files = Path(__file__).resolve().parent.parent / "pddl_testing_files"
    domain, problem = files / "deliver_domain.pddl", files / "deliver_problem.pddl"
    trace = UniformWalkSampling(domain, problem, seed=3, max_actions=4).generate_trace(0)
    write_trace(tmp_path / "t.json", trace)
    read = read_trace(tmp_path / "t.json", domain, problem)
    truck = ObjectType("truck", ObjectType("vehicle", ObjectType("locatable")))
    objects = {o.name: o for f in read[0].state for o in f.objects}
    assert objects["t1"] == PlanningObject("t1", truck)
    assert objects["p1"].obj_type.is_subtype_of(ObjectType("locatable"))
    assert read[0].state == trace[0].state


def test_partial_tokens_round_trip(tmp_path, domain, problem):
    trace = walk(domain, problem)
    tokens = trace.tokenize(PartialObservation, percent_missing=0.4, rng=random.Random(2))
    write_trace(tmp_path / "t.json", tokens)
    read = read_trace(tmp_path / "t.json", domain, problem)
    assert state_values(read) == [
        {str(f): t.state[f] for f in t.state} for t in tokens
    ]
    again = read.tokenize(PartialObservation, percent_missing=0)
    assert [t.state for t in again] == [t.state for t in tokens]
    assert isinstance(read[0].state, PartialState)


def test_noisy_tokens_round_trip(tmp_path, domain, problem):
    trace = walk(domain, problem)
    tokens = trace.tokenize(NoisyObservation, percent_noisy=0.3, rng=random.Random(4))
    write_trace(tmp_path / "t.json", tokens)
    read = read_trace(tmp_path / "t.json", domain, problem)
    assert [s.state for s in read] == [t.state for t in tokens]
    assert "unknown" not in json.loads((tmp_path / "t.json").read_text())["states"][0]


def test_action_tokens_round_trip(tmp_path, domain, problem):
    trace = walk(domain, problem)
    tokens = trace.tokenize(ActionObservation)
    write_trace(tmp_path / "t.json", tokens)
    data = json.loads((tmp_path / "t.json").read_text())
    assert "states" not in data
    read = read_trace(tmp_path / "t.json", domain, problem)
    assert len(read) == len(trace)
    assert all(len(s.state) == 0 for s in read)
    assert [t.action for t in read.tokenize(ActionObservation)] == [t.action for t in tokens]


def test_identity_tokens_round_trip(tmp_path, domain, problem):
    trace = walk(domain, problem)
    write_trace(tmp_path / "t.json", trace.tokenize(IdentityObservation))
    assert read_trace(tmp_path / "t.json", domain, problem) == trace


def test_action_only_file_reads_against_a_shell_without_predicates(tmp_path, domain, problem):
    write_trace(tmp_path / "t.json", walk(domain, problem).tokenize(ActionObservation))
    read = read_trace(tmp_path / "t.json", DomainParser()(ACTION_ONLY_SHELL_TEXT))
    assert read[0].action.name == "drive"
    assert read[0].action.objects[0].obj_type == ObjectType("Truck", ObjectType("vehicle"))


def test_trace_of_length_zero_round_trips(tmp_path, domain, problem):
    trace = walk(domain, problem)
    single = Trace([Step(trace[0].state, None, 1)])
    write_trace(tmp_path / "t.json", single)
    data = json.loads((tmp_path / "t.json").read_text())
    assert data["actions"] == [] and len(data["states"]) == 1
    assert read_trace(tmp_path / "t.json", domain, problem) == single


def test_read_traces_returns_a_trace_list(tmp_path, domain, problem):
    paths = []
    for i in range(3):
        paths.append(tmp_path / f"{i:04}.json")
        write_trace(paths[-1], walk(domain, problem, index=i), problem=f"p{i}")
    traces = read_traces(paths, domain, problem)
    assert isinstance(traces, TraceList)
    assert [t.problem_id for t in traces] == ["p0", "p1", "p2"]
    assert list(traces) == [walk(domain, problem, index=i) for i in range(3)]


# -- the bytes written ---------------------------------------------------------


def test_output_is_canonical(tmp_path, domain, problem):
    trace = walk(domain, problem, max_actions=1)
    write_trace(tmp_path / "t.json", trace, problem="p03")
    text = (tmp_path / "t.json").read_text()
    data = json.loads(text)
    assert text == json.dumps(data, indent=2) + "\n"
    assert list(data) == ["format_version", "problem", "states", "actions"]
    assert data["format_version"] == 1
    assert data["states"][0]["true"] == sorted(data["states"][0]["true"])
    assert "(at t1 L1)" in data["states"][0]["true"]
    assert "(road depot L1)" in data["states"][0]["true"]
    assert data["actions"][0].startswith("(drive t1 ")


def test_problem_is_left_out_when_there_is_none(tmp_path, domain, problem):
    write_trace(tmp_path / "t.json", walk(domain, problem))
    assert "problem" not in json.loads((tmp_path / "t.json").read_text())


def test_problem_falls_back_to_the_trace_problem_id(tmp_path, domain, problem):
    trace = walk(domain, problem)
    trace.problem_id = "p07"
    write_trace(tmp_path / "t.json", trace)
    assert json.loads((tmp_path / "t.json").read_text())["problem"] == "p07"
    write_trace(tmp_path / "u.json", trace, problem="p08")
    assert read_trace(tmp_path / "u.json", domain, problem).problem_id == "p08"


def test_partial_states_always_list_unknowns(tmp_path, domain, problem):
    tokens = walk(domain, problem).tokenize(PartialObservation, percent_missing=0)
    write_trace(tmp_path / "t.json", tokens)
    states = json.loads((tmp_path / "t.json").read_text())["states"]
    assert all(s["unknown"] == [] for s in states)


def test_writing_twice_gives_the_same_bytes(tmp_path, domain, problem):
    write_trace(tmp_path / "a.json", walk(domain, problem))
    write_trace(tmp_path / "b.json", walk(domain, problem))
    assert (tmp_path / "a.json").read_bytes() == (tmp_path / "b.json").read_bytes()


# -- what the writer refuses ------------------------------------------------------


def test_writer_rejects_states_with_different_atom_sets(tmp_path, domain, problem):
    trace = walk(domain, problem)
    first = next(iter(trace[1].state))
    del trace[1].state[first]
    with pytest.raises(ValueError, match="atom"):
        write_trace(tmp_path / "t.json", trace)


def test_writer_rejects_mixing_stateless_and_stateful_tokens(tmp_path, domain, problem):
    trace = walk(domain, problem)
    tokens = trace.tokenize(IdentityObservation)
    tokens[1].state = None
    with pytest.raises(ValueError, match="state"):
        write_trace(tmp_path / "t.json", tokens)


def test_writer_rejects_atomic_tokens(tmp_path, domain, problem):
    tokens = walk(domain, problem).tokenize(AtomicPartialObservation, percent_missing=0.5)
    with pytest.raises(TypeError):
        write_trace(tmp_path / "t.json", tokens)


def test_writer_rejects_a_missing_or_extra_action(tmp_path, domain, problem):
    trace = walk(domain, problem)
    trace[-1].action = trace[0].action
    with pytest.raises(ValueError, match="action"):
        write_trace(tmp_path / "t.json", trace)
    trace = walk(domain, problem)
    trace[0].action = None
    with pytest.raises(ValueError, match="action"):
        write_trace(tmp_path / "t.json", trace)


def test_writer_rejects_an_empty_trace(tmp_path):
    with pytest.raises(ValueError):
        write_trace(tmp_path / "t.json", Trace())


def test_writer_rejects_names_that_are_not_canonical(tmp_path):
    bad = GroundedFluent("on top", [PlanningObject("a", ObjectType("object"))])
    with pytest.raises(ValueError, match="name"):
        write_trace(tmp_path / "t.json", Trace([Step(State({bad: True}), None, 1)]))


def test_writer_rejects_two_fluents_with_the_same_string(tmp_path):
    first = GroundedFluent("p", [PlanningObject("a", ObjectType("t1"))])
    second = GroundedFluent("p", [PlanningObject("a", ObjectType("t2"))])
    state = State({first: True})
    state.fluents[second] = False
    with pytest.raises(ValueError, match="twice"):
        write_trace(tmp_path / "t.json", Trace([Step(state, None, 1)]))


def test_writer_rejects_a_non_boolean_value(tmp_path):
    fluent = GroundedFluent("p", [PlanningObject("a", ObjectType("object"))])
    with pytest.raises(ValueError, match="value"):
        write_trace(tmp_path / "t.json", Trace([Step(State({fluent: 1}), None, 1)]))


# -- what the reader refuses --------------------------------------------------------


def good(domain, problem, tmp_path):
    write_trace(tmp_path / "good.json", walk(domain, problem, max_actions=2))
    return json.loads((tmp_path / "good.json").read_text())


def partial_good(domain, problem, tmp_path):
    tokens = walk(domain, problem, max_actions=2).tokenize(
        PartialObservation, percent_missing=0.5, rng=random.Random(1)
    )
    write_trace(tmp_path / "good.json", tokens)
    return json.loads((tmp_path / "good.json").read_text())


def first_true(data):
    return data["states"][0]["true"]


BREAKAGES = {
    "unknown version": lambda d: d.update(format_version=2),
    "boolean version": lambda d: d.update(format_version=True),
    "missing version": lambda d: d.pop("format_version"),
    "missing actions": lambda d: d.pop("actions"),
    "unknown key": lambda d: d.update(extra=1),
    "problem not a string": lambda d: d.update(problem=3),
    "not canonical, padding": lambda d: first_true(d).__setitem__(0, "( at t1 L1)"),
    "not canonical, double space": lambda d: first_true(d).__setitem__(0, "(at  t1 L1)"),
    "not canonical, no parens": lambda d: first_true(d).__setitem__(0, "at t1 L1"),
    "not canonical, empty": lambda d: first_true(d).__setitem__(0, "()"),
    "action not canonical": lambda d: d["actions"].__setitem__(0, d["actions"][0] + " "),
    "unsorted atoms": lambda d: first_true(d).reverse(),
    "duplicate atom": lambda d: first_true(d).insert(0, first_true(d)[0]),
    "unknown predicate": lambda d: first_true(d).insert(0, "(At t1 L1)"),
    "wrong predicate arity": lambda d: first_true(d).insert(0, "(at t1)"),
    "unknown object": lambda d: first_true(d).insert(0, "(at t9 L1)"),
    "wrong argument type": lambda d: first_true(d).insert(0, "(at L1 L1)"),
    "unknown action": lambda d: d["actions"].__setitem__(0, "(fly t1 L1 L2)"),
    "wrong action arity": lambda d: d["actions"].__setitem__(0, "(drive t1 L1)"),
    "wrong action argument type": lambda d: d["actions"].__setitem__(0, "(drive L1 L1 L2)"),
    "too few states": lambda d: d["states"].pop(),
    "too many states": lambda d: d["states"].append({"true": []}),
    "unknown state key": lambda d: d["states"][0].update(maybe=[]),
    "state missing true": lambda d: d["states"][0].pop("true"),
    "mixed state forms": lambda d: d["states"][0].update(unknown=[]),
    "states not a list": lambda d: d.update(states={}),
    "atom not a string": lambda d: first_true(d).insert(0, 3),
}


@pytest.mark.parametrize("breakage", sorted(BREAKAGES))
def test_reader_rejects(breakage, tmp_path, domain, problem):
    data = good(domain, problem, tmp_path)
    if breakage in ("unsorted atoms",):
        assert len(first_true(data)) > 1
    BREAKAGES[breakage](data)
    write_json(tmp_path / "bad.json", data)
    with pytest.raises(InvalidTraceFile):
        read_trace(tmp_path / "bad.json", domain, problem)


def test_reader_rejects_an_atom_both_true_and_unknown(tmp_path, domain, problem):
    data = partial_good(domain, problem, tmp_path)
    state = next(s for s in data["states"] if s["unknown"])
    state["true"] = sorted(state["true"] + [state["unknown"][0]])
    write_json(tmp_path / "bad.json", data)
    with pytest.raises(InvalidTraceFile, match="unknown"):
        read_trace(tmp_path / "bad.json", domain, problem)


def test_reader_rejects_text_that_is_not_json(tmp_path, domain, problem):
    (tmp_path / "bad.json").write_text("{")
    with pytest.raises(InvalidTraceFile):
        read_trace(tmp_path / "bad.json", domain, problem)


def test_reader_rejects_states_against_a_shell_without_predicates(tmp_path, domain, problem):
    write_trace(tmp_path / "t.json", walk(domain, problem))
    with pytest.raises(InvalidTraceFile, match="predicate"):
        read_trace(tmp_path / "t.json", DomainParser()(ACTION_ONLY_SHELL_TEXT))


def test_reader_is_case_sensitive(tmp_path, domain, problem):
    data = good(domain, problem, tmp_path)
    data["actions"][0] = data["actions"][0].replace("drive", "Drive")
    write_json(tmp_path / "bad.json", data)
    with pytest.raises(InvalidTraceFile, match="Drive"):
        read_trace(tmp_path / "bad.json", domain, problem)


# -- the documented limit -------------------------------------------------------------


def test_statics_left_out_of_states_read_back_as_false(tmp_path):
    """Round trips are exact only when states cover the full atom set."""
    domain = DomainParser()(DOMAIN_TEXT)
    problem = ProblemParser()(PROBLEM_TEXT)
    trace = VanillaSampling(dom=domain, prob=problem, plan_len=2, num_traces=1).traces[0]
    write_trace(tmp_path / "t.json", trace)
    read = read_trace(tmp_path / "t.json", domain, problem)
    road = next(f for f in read[0].state if f.name == "road" and f.objects[0].name == "L1")
    assert read[0].state[road] is False
    assert road not in trace[0].state.fluents


import random
from pathlib import Path

import pytest
from pddl import parse_problem

from macq.core import GroundedFluent, ObjectType, PlanningObject
from macq.generate.pddl import Generator, VanillaSampling
from macq.generate.pddl.generator import InvalidGoalFluent

DOMAIN = """
(define (domain Probe)
  (:requirements :strips :typing :negative-preconditions)
  (:types Box place - object)
  (:predicates (at ?b - Box ?p - place) (link ?a ?b - place) (sealed ?b - Box) (done))
  (:action Move
    :parameters (?b - Box ?from ?to - place)
    :precondition (and (at ?b ?from) (link ?from ?to) (not (sealed ?b)))
    :effect (and (at ?b ?to) (not (at ?b ?from))))
  (:action seal
    :parameters (?b - Box)
    :precondition (not (sealed ?b))
    :effect (sealed ?b)))
"""

PROBLEM = """
(define (problem probe-1)
  (:domain Probe)
  (:objects B1 - Box L1 L2 - place)
  (:init (at B1 L1) (link L1 L2))
  (:goal (at B1 L2)))
"""

UNTYPED_DOMAIN = """
(define (domain flat)
  (:requirements :strips)
  (:predicates (on ?x))
  (:action flip :parameters (?x) :precondition (on ?x) :effect (not (on ?x))))
"""

UNTYPED_PROBLEM = """
(define (problem flat-1) (:domain flat) (:objects a) (:init (on a)) (:goal (on a)))
"""

DEAD_END_DOMAIN = """
(define (domain trap)
  (:requirements :strips)
  (:predicates (alive))
  (:action trap :parameters () :precondition (alive) :effect (not (alive)))
  (:action step :parameters () :precondition (alive) :effect (alive)))
"""

DEAD_END_PROBLEM = """
(define (problem trap-1) (:domain trap) (:init (alive)) (:goal (alive)))
"""

COST_DOMAIN = """
(define (domain costly)
  (:requirements :strips :action-costs)
  (:predicates (on))
  (:functions (total-cost) - number)
  (:action flip :parameters () :precondition (on)
    :effect (and (not (on)) (increase (total-cost) 1))))
"""

COST_PROBLEM = """
(define (problem costly-1) (:domain costly) (:init (on) (= (total-cost) 0))
  (:goal (on)) (:metric minimize (total-cost)))
"""


def write(tmp_path, domain=DOMAIN, problem=PROBLEM):
    dom, prob = tmp_path / "domain.pddl", tmp_path / "problem.pddl"
    dom.write_text(domain)
    prob.write_text(problem)
    return str(dom), str(prob)


def fluent(name, *objects):
    return GroundedFluent(name, [PlanningObject(o, ObjectType("object")) for o in objects])


def names(fluents):
    return {
        " ".join([f.name, *[o.name for o in f.objects]]) for f in fluents
    }


def test_states_list_every_type_consistent_atom_of_changing_predicates(tmp_path):
    dom, prob = write(tmp_path)

    assert names(Generator(dom, prob).grounded_fluents) == {
        "at B1 L1",
        "at B1 L2",
        "sealed B1",
    }


def test_static_predicates_are_listed_on_request(tmp_path):
    dom, prob = write(tmp_path)

    fluents = names(Generator(dom, prob, ignore_static_fluents=False).grounded_fluents)

    assert {"link L1 L1", "link L1 L2", "link L2 L1", "link L2 L2", "done"} < fluents


def test_names_keep_their_case_and_declared_types(tmp_path):
    dom, prob = write(tmp_path)
    generator = VanillaSampling(dom, prob, plan_len=2)

    plan_file = tmp_path / "plan.ipc"
    plan_file.write_text("(Move B1 L1 L2)\n")
    plan = generator.generate_plan(from_ipc_file=True, filename=str(plan_file))
    action = generator.generate_single_trace_from_plan(plan)[0].action

    assert action.name == "Move"
    assert [o.details() for o in action.obj_params] == [
        "Box B1",
        "place L1",
        "place L2",
    ]


def test_untyped_objects_have_the_type_object(tmp_path):
    dom, prob = write(tmp_path, UNTYPED_DOMAIN, UNTYPED_PROBLEM)

    [only] = Generator(dom, prob).grounded_fluents

    assert only.objects[0].obj_type == ObjectType()


def test_negative_preconditions_are_left_out_of_trace_actions(tmp_path):
    dom, prob = write(tmp_path)
    generator = VanillaSampling(dom, prob, plan_len=2, observe_pres_effs=True)

    plan_file = tmp_path / "plan.ipc"
    plan_file.write_text("(Move B1 L1 L2)\n")
    plan = generator.generate_plan(from_ipc_file=True, filename=str(plan_file))
    action = generator.generate_single_trace_from_plan(plan)[0].action

    assert names(action.precond) == {"at B1 L1", "link L1 L2"}
    assert names(action.add) == {"at B1 L2"}
    assert names(action.delete) == {"at B1 L1"}


def test_plans_match_regardless_of_case(tmp_path):
    dom, prob = write(tmp_path)
    generator = Generator(dom, prob)

    plan_file = tmp_path / "plan.ipc"
    plan_file.write_text("(move b1 l1 l2)\n; cost = 1 (unit cost)\n")
    plan = generator.generate_plan(from_ipc_file=True, filename=str(plan_file))

    assert str(plan) == "(Move B1 L1 L2)"


def test_unknown_plan_steps_are_rejected(tmp_path):
    from macq.generate.pddl.generator import InvalidPlanStep

    dom, prob = write(tmp_path)
    generator = Generator(dom, prob)

    plan_file = tmp_path / "plan.ipc"
    plan_file.write_text("(fly b1 l1 l2)\n")

    with pytest.raises(InvalidPlanStep):
        generator.generate_plan(from_ipc_file=True, filename=str(plan_file))


def test_changing_the_initial_state_keeps_static_atoms(tmp_path):
    dom, prob = write(tmp_path)
    generator = Generator(dom, prob)
    new_dom, new_prob = str(tmp_path / "d.pddl"), str(tmp_path / "p.pddl")

    generator.change_init([fluent("at", "B1", "L2")], new_dom, new_prob)

    written = Path(new_prob).read_text().lower()
    assert "(link l1 l2)" in written
    assert "(at b1 l2)" in written
    assert "(at b1 l1)" not in written


def test_changed_goals_are_written_as_parseable_pddl(tmp_path):
    dom, prob = write(tmp_path)
    generator = Generator(dom, prob)
    new_dom, new_prob = str(tmp_path / "d.pddl"), str(tmp_path / "p.pddl")

    generator.change_goal([fluent("sealed", "B1")], new_dom, new_prob)

    assert "(sealed B1)" in str(parse_problem(new_prob).goal)


def test_goals_need_only_name_atoms_of_the_problem(tmp_path):
    dom, prob = write(tmp_path)
    generator = Generator(dom, prob)
    new_dom, new_prob = str(tmp_path / "d.pddl"), str(tmp_path / "p.pddl")

    # L2 can never be left, but the atom exists
    generator.change_goal([fluent("at", "B1", "L1")], new_dom, new_prob)

    with pytest.raises(InvalidGoalFluent):
        generator.change_goal([fluent("at", "B1", "L9")], new_dom, new_prob)


def test_a_walk_that_reaches_a_dead_end_restarts_from_the_initial_state(
    tmp_path, monkeypatch
):
    dom, prob = write(tmp_path, DEAD_END_DOMAIN, DEAD_END_PROBLEM)
    generator = VanillaSampling(dom, prob, plan_len=3)
    choices = []

    def trap_once(actions):
        choices.append(actions)
        wanted = "trap" if len(choices) == 1 else "step"
        return next(a for a in actions if str(a.name).startswith(wanted))

    monkeypatch.setattr(random, "choice", trap_once)

    trace = generator.generate_single_trace_setup(num_seconds=5, plan_len=3)()

    assert [step.action.name for step in trace[:-1]] == ["step", "step"]


def test_domains_outside_the_supported_fragment_are_rejected(tmp_path):
    dom, prob = write(tmp_path, COST_DOMAIN, COST_PROBLEM)

    with pytest.raises(NotImplementedError):
        Generator(dom, prob)

from pathlib import Path

import pytest
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser

from macq.core import ObjectType, PlanningObject
from macq.utils.pddl_objects import object_types, planning_objects

FILES = Path(__file__).resolve().parent.parent / "pddl_testing_files"


def deliver():
    return (
        DomainParser()((FILES / "deliver_domain.pddl").read_text()),
        ProblemParser()((FILES / "deliver_problem.pddl").read_text()),
    )


def test_object_types_keep_their_parent_chain():
    domain, _ = deliver()
    types = object_types(domain)
    locatable = ObjectType("locatable")
    assert types["truck"] == ObjectType("truck", ObjectType("vehicle", locatable))
    assert types["package"] == ObjectType("package", locatable)
    assert types["location"] == ObjectType("location")
    assert types["object"] == ObjectType()


def test_objects_share_one_type_per_name():
    domain, problem = deliver()
    objects = planning_objects(domain, problem.objects)
    assert objects["t1"] == PlanningObject("t1", object_types(domain)["truck"])
    assert objects["p1"].obj_type is objects["p2"].obj_type


def test_untyped_objects_have_the_type_object():
    domain = DomainParser()("(define (domain d) (:requirements :strips) (:predicates (p ?x)))")
    problem = ProblemParser()("(define (problem q) (:domain d) (:objects a) (:init) (:goal (p a)))")
    assert planning_objects(domain, problem.objects) == {"a": PlanningObject("a", ObjectType())}

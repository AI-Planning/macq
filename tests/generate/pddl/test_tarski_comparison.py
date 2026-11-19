"""Temporary check that pddl-utils and tarski agree, removed along with tarski."""

import random
import re
from pathlib import Path

import pddlutils as pu
import pytest
import requests
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser
from tarski.grounding.lp_grounding import ground_problem_schemas_into_plain_operators
from tarski.io import PDDLReader
from tarski.search import GroundForwardSearchModel
from tarski.search.operations import progress
from tarski.syntax.formulas import Atom

from macq.generate.pddl.planning_domains_api import get_problem

FILES = Path(__file__).parent.parent.parent / "pddl_testing_files"
LOCAL = {"door": ("door_dom.pddl", "door_prob.pddl")}
REMOTE = [1801, 4154, 2688, 2336, 212]
STEPS = 30


def load(case):
    if case in LOCAL:
        return tuple((FILES / name).read_text() for name in LOCAL[case])
    problem = get_problem(case, formalism="classical")
    return (
        requests.get(problem["domain_url"], timeout=30).text,
        requests.get(problem["problem_url"], timeout=30).text,
    )


def tarski_signature(operator):
    return tuple(word.lower() for word in re.findall(r"[^(), ]+", operator.name))


def pddl_signature(action):
    names = [action.name, *[term.name for term in action.parameters]]
    return tuple(str(name).lower() for name in names)


def tarski_atoms(state):
    return {
        tuple(
            str(part).lower()
            for part in (atom.predicate.name, *[t.name for t in atom.subterms])
        )
        for atom in state.as_atoms()
        if isinstance(atom, Atom) and isinstance(atom.predicate.name, str)
    }


def pddl_atoms(state):
    return {
        tuple(str(part).lower() for part in (atom.name, *[t.name for t in atom.terms]))
        for atom in state
    }


@pytest.mark.parametrize("case", [*LOCAL, *REMOTE])
def test_both_stacks_agree_along_a_random_walk(case):
    domain_text, problem_text = load(case)

    reader = PDDLReader(raise_on_error=True)
    reader.parse_domain_string(domain_text)
    problem = reader.parse_instance_string(problem_text)
    model = GroundForwardSearchModel(
        problem, ground_problem_schemas_into_plain_operators(problem)
    )
    task = pu.Task(DomainParser()(domain_text), ProblemParser()(problem_text))

    generator = random.Random(0)
    tarski_state = problem.init
    pddl_state = task.initial_state
    for _ in range(STEPS):
        assert tarski_atoms(tarski_state) == pddl_atoms(pddl_state)

        operators = {tarski_signature(o): o for o in model.applicable(tarski_state)}
        actions = {pddl_signature(a): a for a in task.applicable_actions(pddl_state)}
        assert set(operators) == set(actions)
        if not actions:
            break

        chosen = generator.choice(sorted(actions))
        tarski_state = progress(tarski_state, operators[chosen])
        pddl_state = task.progress(pddl_state, actions[chosen])

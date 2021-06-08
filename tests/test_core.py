import pytest
from typing import List, Dict
from tests.utils.generators import *
from macq.trace import (
    PlanningObject,
    Fluent,
    Action,
    Step,
    State,
    Trace,
    SAS,
    TraceList,
)
from macq.observation import IdentityObservation
from pathlib import Path
from macq.utils.timer import TraceSearchTimeOut
from macq.generate.pddl import VanillaSampling

MissingGenerator = TraceList.MissingGenerator


def get_fluent_obj(fluents: List[Fluent]):
    """
    Extracts the objects used by the given fluents.

    Arguments
    ---------
    fluents : List of Fluents
        The fluents to extract the objects from.

    Returns
    -------
    objects : List of CustomObjects
        The list of objects used by the given fluents.
    """
    objects = []
    for fluent in fluents:
        for obj in fluent.objects:
            objects.append(obj)
    return objects


# test the timer wrapper on vanilla trace generation
# def test_timer_vanilla_wrapper():
#     # exit out to the base macq folder so we can get to /tests
#     base = Path(__file__).parent.parent
#     dom = (base / "tests/pddl_testing_files/playlist_domain.pddl").resolve()
#     prob = (base / "tests/pddl_testing_files/playlist_problem.pddl").resolve()

#     with pytest.raises(TraceSearchTimeOut):
#         VanillaSampling(dom, prob, 10, 5)


def test_trace_list():
    trace_list = generate_test_trace_list(5)

    assert len(trace_list) == 5

    with pytest.raises(MissingGenerator):
        trace_list.generate_more(5)

    first = trace_list[0]
    trace_list.generator = generate_test_trace_list
    trace_list.generate_more(5)
    assert len(trace_list) == 10
    assert trace_list[0] is first

    action = trace_list[0].steps[0].action
    usages = trace_list.get_usage(action)
    for i, trace in enumerate(trace_list):
        assert usages[i] == trace.get_usage(action)

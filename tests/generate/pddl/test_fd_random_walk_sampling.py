import pytest
from pathlib import Path
from macq.generate.pddl import FDRandomWalkSampling

from macq.generate.pddl.generator import InvalidGoalFluent
from macq.utils import InvalidNumberOfTraces, InvalidPlanLength
from macq.trace import Fluent, PlanningObject, TraceList
from macq.utils import TraceSearchTimeOut, InvalidTime


def test_fd_random_samples():

    sampler = FDRandomWalkSampling(problem_id=212, num_traces=3, max_time=10)
    assert len(sampler.traces) == 3

    FDRandomWalkSampling(problem_id=212, init_h=5, num_traces=3, max_time=10)
    assert len(sampler.traces) == 3



if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).absolute().parent.parent.parent

    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    sampler = FDRandomWalkSampling(dom=dom, prob=prob, num_traces=10)
    traces = sampler.traces
    traces.generate_more(3)

    dom = str((base / "pddl_testing_files/playlist_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/playlist_problem.pddl").resolve())
    FDRandomWalkSampling(dom=dom, prob=prob, num_traces=10, max_time=5)

    new_blocks_dom = str(
        (base / "generated_testing_files/new_blocks_dom.pddl").resolve()
    )
    new_blocks_prob = str(
        (base / "generated_testing_files/new_blocks_prob.pddl").resolve()
    )
    new_game_dom = str((base / "generated_testing_files/new_game_dom.pddl").resolve())
    new_game_prob = str((base / "generated_testing_files/new_game_prob.pddl").resolve())

    # test changing the goal and generating a plan from two local files
    sampler.change_goal(
        {
            Fluent(
                "on", [PlanningObject("object", "f"), PlanningObject("object", "g")]
            ),
        },
        new_blocks_dom,
        new_blocks_prob,
    )
    plan = sampler.generate_plan()
    print(plan)
    print()
    trace = sampler.generate_single_trace_from_plan(plan)
    tracelist = TraceList()
    tracelist.append(trace)
    tracelist.print(wrap="y")

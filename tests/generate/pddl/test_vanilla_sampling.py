import pytest
from pathlib import Path
from macq.generate.pddl import VanillaSampling
from macq.generate.pddl.generator import InvalidGoalFluent
from macq.generate import InvalidNumberOfTraces, InvalidPlanLength
from macq.trace import Fluent, PlanningObject, TraceList
from macq.utils import TraceSearchTimeOut, InvalidTime


def test_invalid_vanilla_sampling():
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/playlist_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/playlist_problem.pddl").resolve())

    with pytest.raises(InvalidPlanLength):
        VanillaSampling(dom=dom, prob=prob, plan_len=-1, num_traces=5)

    with pytest.raises(InvalidNumberOfTraces):
        VanillaSampling(dom=dom, prob=prob, plan_len=5, num_traces=-1)

    with pytest.raises(InvalidGoalFluent):
        vanilla = VanillaSampling(dom=dom, prob=prob, plan_len=5, num_traces=1)
        # test changing the goal and generating a plan from two local files
        vanilla.change_goal(
            {
                Fluent(
                    "on", [PlanningObject("object", "a"), PlanningObject("object", "z")]
                ),
            },
            "new_blocks_dom.pddl",
            "new_blocks_prob.pddl",
        )
    
    with pytest.raises(TraceSearchTimeOut):
        VanillaSampling(dom=dom, prob=prob, plan_len=10, num_traces=1, max_time=5)
    
    with pytest.raises(InvalidTime):
        VanillaSampling(dom=dom, prob=prob, plan_len=10, num_traces=1, max_time=0)


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent

    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())
    vanilla = VanillaSampling(dom=dom, prob=prob, plan_len=7, num_traces=10)
    traces = vanilla.traces
    traces.generate_more(3)
    
    new_blocks_dom = str((base / "generated_testing_files/new_blocks_dom.pddl").resolve())
    new_blocks_prob = str((base / "generated_testing_files/new_blocks_prob.pddl").resolve())
    new_game_dom = str((base / "generated_testing_files/new_game_dom.pddl").resolve())
    new_game_prob = str((base / "generated_testing_files/new_game_prob.pddl").resolve())

    # test changing the goal and generating a plan from two local files
    vanilla.change_goal(
        {
            Fluent(
                "on", [PlanningObject("object", "f"), PlanningObject("object", "g")]
            ),
        },
        new_blocks_dom,
        new_blocks_prob,
    )
    plan = vanilla.generate_plan()
    print(plan)
    print()
    trace = vanilla.generate_single_trace_from_plan(plan)
    tracelist = TraceList()
    tracelist.append(trace)
    tracelist.print(wrap="y")

    # test changing the goal and generating a plan from files extracted from a problem ID
    vanilla = VanillaSampling(problem_id=123, plan_len=7, num_traces=10)
    vanilla.change_goal(
        {
            Fluent(
                "at",
                [
                    PlanningObject("stone", "stone-11"),
                    PlanningObject("location", "pos-10-07"),
                ],
            )
        },
        new_game_dom,
        new_game_prob,
    )
    plan = vanilla.generate_plan()
    print(plan)
    print()
    trace = vanilla.generate_single_trace_from_plan(plan)
    tracelist = TraceList()
    tracelist.append(trace)
    tracelist.print(wrap="y")


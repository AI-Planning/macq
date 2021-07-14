import pytest
from pathlib import Path
from macq.generate.pddl import GoalTracesSampling
from macq.generate.pddl.generator import InvalidGoalFluent
from macq.generate import InvalidNumberOfTraces, InvalidPlanLength
from macq.trace import Fluent, PlanningObject


def test_invalid_goal_sampling():
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/playlist_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/playlist_problem.pddl").resolve())

    with pytest.raises(InvalidPlanLength):
        GoalTracesSampling(dom=dom, prob=prob, plan_len=-1, num_traces=5)

    with pytest.raises(InvalidNumberOfTraces):
        GoalTracesSampling(dom=dom, prob=prob, plan_len=5, num_traces=-1)

    with pytest.raises(InvalidGoalFluent):
        vanilla = GoalTracesSampling(dom=dom, prob=prob, plan_len=5, num_traces=1)
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


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    # test sampling using the original goal from a local PDDL problem file

    goal_traces_sampler = GoalTracesSampling(dom=dom, prob=prob)
    goal_traces = goal_traces_sampler.traces
    goal_traces.print(wrap="y")
    print()

    # test changing the goal and regenerating traces from local PDDL files
    goal_traces_sampler.change_goal(
        {
            Fluent(
                "on", [PlanningObject("object", "c"), PlanningObject("object", "e")]
            ),
            Fluent(
                "on", [PlanningObject("object", "a"), PlanningObject("object", "b")]
            ),
        },
        "new_blocks_dom.pddl",
        "new_blocks_prob.pddl",
    )
    goal_traces = goal_traces_sampler.generate_traces()
    goal_traces.print(wrap="y")
    print()

    # test sampling using the goal from the problem file extracted from a problem ID
    goal_traces_sampler = GoalTracesSampling(problem_id=123)
    goal_traces = goal_traces_sampler.traces
    goal_traces.print(wrap="y")
    print()

    # test changing the goal and regenerating traces from files extracted from a problem ID
    goal_traces_sampler.change_goal(
        {
            Fluent(
                "at",
                [
                    PlanningObject("stone", "stone-11"),
                    PlanningObject("location", "pos-10-07"),
                ],
            )
        },
        "new_game_dom.pddl",
        "new_game_prob.pddl",
    )
    goal_traces = goal_traces_sampler.generate_traces()
    goal_traces.print(wrap="y")
    print()

    # test getting multiple traces and altering length
    goal_traces_sampler = GoalTracesSampling(problem_id=123, plan_len=3, num_traces=4)
    goal_traces = goal_traces_sampler.traces
    goal_traces.print(wrap="y")
    print()

    # test getting multiple traces and altering length
    goal_traces_sampler = GoalTracesSampling(problem_id=123, plan_len=1000)
    goal_traces = goal_traces_sampler.traces
    goal_traces.print(wrap="y")
    print()

import pytest
from pathlib import Path
from macq.generate.pddl import TraceFromGoal
from macq.generate.pddl.generator import InvalidGoalFluent
from macq.utils import InvalidNumberOfTraces, InvalidPlanLength
from macq.trace import Fluent, PlanningObject


def test_invalid_goal_change():
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/playlist_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/playlist_problem.pddl").resolve())

    with pytest.raises(InvalidGoalFluent):
        goal_traces = TraceFromGoal(dom=dom, prob=prob)
        # test changing the goal and generating a plan from two local files
        goal_traces.change_goal(
            {
                Fluent(
                    "on", [PlanningObject("object", "a"), PlanningObject("object", "z")]
                ),
            },
            "new_blocks_dom.pddl",
            "new_blocks_prob.pddl",
        )

def test_parameter_order():
    # assert accuracy
    goal_generator = TraceFromGoal(problem_id=4398)
    goal_generator.change_init(
        {
            Fluent("on", [PlanningObject("object", "c"), PlanningObject("object", "a")]),
            Fluent("clear", [PlanningObject("object", "c")]),
            Fluent("clear", [PlanningObject("object", "b")]),
            Fluent("ontable", [PlanningObject("object", "b")]),
            Fluent("ontable", [PlanningObject("object", "a")]),
            Fluent("handempty", [])
        }
    )
    goal_generator.change_goal({
        Fluent("on", [PlanningObject("object", "b"), PlanningObject("object", "a")]),
    })
    trace = goal_generator.generate_trace()
    # assert object order
    for act in trace.actions:
        if act.name == "unstack":
            assert act.obj_params == [PlanningObject("object", "c"), PlanningObject("object", "a")]
        elif act.name == "stack":
            assert act.obj_params == [PlanningObject("object", "b"), PlanningObject("object", "a")]   

if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    new_blocks_dom = str(
        (base / "generated_testing_files/new_blocks_dom.pddl").resolve()
    )
    new_blocks_prob = str(
        (base / "generated_testing_files/new_blocks_prob.pddl").resolve()
    )
    new_game_dom = str((base / "generated_testing_files/new_game_dom.pddl").resolve())
    new_game_prob = str((base / "generated_testing_files/new_game_prob.pddl").resolve())

    # test sampling using the original goal from a local PDDL problem file
    goal_traces_sampler = TraceFromGoal(dom=dom, prob=prob)
    goal_trace = goal_traces_sampler.trace
    true_f = [str(f) for f in goal_trace[-1].state if goal_trace[-1].state[f]]
    print(true_f)
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
        # new_blocks_dom,
        # new_blocks_prob,
    )
    goal_traces_sampler.generate_trace()
    goal_trace = goal_traces_sampler.trace
    true_f = [str(f) for f in goal_trace[-1].state if goal_trace[-1].state[f]]
    print(true_f)
    print()

    # test changing the goal and regenerating traces from files extracted from a problem ID
    goal_traces_sampler = TraceFromGoal(problem_id=123)
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
        new_game_dom,
        new_game_prob,
    )
    goal_traces = goal_traces_sampler.generate_trace()
    goal_trace = goal_traces_sampler.trace
    true_f = [str(f) for f in goal_trace[-1].state if goal_trace[-1].state[f]]
    print(true_f)

    # test generating traces with action preconditions/effects known
    goal_traces = TraceFromGoal(dom=dom, prob=prob, observe_pres_effs=True).trace

test_parameter_order()
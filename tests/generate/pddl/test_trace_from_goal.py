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
    def fluent(name, *objects):
        return Fluent(name, [PlanningObject("object", o) for o in objects])

    # assert accuracy
    goal_generator = TraceFromGoal(problem_id=4154)
    goal_generator.change_init(
        {
            fluent("room", "rooma"),
            fluent("room", "roomb"),
            fluent("ball", "ball1"),
            fluent("ball", "ball2"),
            fluent("ball", "ball3"),
            fluent("ball", "ball4"),
            fluent("gripper", "left"),
            fluent("gripper", "right"),
            fluent("at-robby", "rooma"),
            fluent("free", "left"),
            fluent("free", "right"),
            fluent("at", "ball1", "rooma"),
            fluent("at", "ball2", "roomb"),
            fluent("at", "ball3", "roomb"),
            fluent("at", "ball4", "roomb"),
        }
    )
    goal_generator.change_goal({fluent("at", "ball1", "roomb")})
    trace = goal_generator.generate_trace()
    # assert object order
    names = {act.name: [o.name for o in act.obj_params] for act in trace.actions}
    assert names["pick"][:2] == ["ball1", "rooma"]
    assert names["move"] == ["rooma", "roomb"]
    assert names["drop"][:2] == ["ball1", "roomb"]


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
    goal_traces_sampler = TraceFromGoal(problem_id=1801)
    goal_traces_sampler.change_goal(
        {
            Fluent(
                "at",
                [
                    PlanningObject("rover", "rover0"),
                    PlanningObject("waypoint", "waypoint3"),
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

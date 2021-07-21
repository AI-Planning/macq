import pytest
from pathlib import Path
from macq.generate.pddl import VanillaSampling
from macq.generate.pddl.generator import InvalidGoalFluent
from macq.generate import InvalidNumberOfTraces, InvalidPlanLength
from macq.trace import Fluent, PlanningObject


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


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())
    vanilla = VanillaSampling(dom=dom, prob=prob, plan_len=20, num_traces=1)

    # test goal sampling
    states_gen = vanilla.goal_sampling(
        num_states=3,
        steps_deep=5,
        plan_complexity=5,
        subset_size_perc=0.1,
        new_domain="new_blocks_dom.pddl",
        new_prob="new_blocks_prob.pddl",
    )

    for s in states_gen:
        print()
        print(states_gen[s])
        print()
        f_sorted = [str(f) for f in s.fluents]
        f_sorted.sort()
        for f in f_sorted:
            print(f)

    # test changing the goal and generating a plan from two local files
    vanilla.change_goal(
        {
            Fluent(
                "on", [PlanningObject("object", "f"), PlanningObject("object", "g")]
            ),
        },
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
    plan = vanilla.generate_plan()
    print(plan)
    print()

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
        "new_game_dom.pddl",
        "new_game_prob.pddl",
    )
    plan = vanilla.generate_plan()
    print(plan)
    print()

import pytest
from pathlib import Path
from macq.generate.pddl import VanillaSampling
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


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())
    vanilla = VanillaSampling(dom=dom, prob=prob, plan_len=7, num_traces=10)

    # test goal sampling
    states_gen = vanilla.goal_sampling(3, 5, 0.2)

    # test change goal
    vanilla.change_goal(
        {
            Fluent(
                "on", [PlanningObject("object", "c"), PlanningObject("object", "e")]
            ),
            Fluent(
                "on", [PlanningObject("object", "a"), PlanningObject("object", "b")]
            ),
        }
    )

    # test generating plans, both from raw pddl files and from a problem ID
    # from raw pddl
    vanilla.generate_plan()
    # from problem ID
    vanilla = VanillaSampling(problem_id=123, plan_len=7, num_traces=10)
    vanilla.generate_plan()

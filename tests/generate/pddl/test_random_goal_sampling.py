from pathlib import Path
from macq.generate.pddl import RandomGoalSampling

if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    random_sampler = RandomGoalSampling(
        dom=dom,
        prob=prob,
        steps_deep=5,
        plan_complexity=5,
        subset_size_perc=0.05,
        num_traces=3,
    )

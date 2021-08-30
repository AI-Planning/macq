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
        num_traces=20,
        steps_deep=20,
        subset_size_perc=0.1,
        enforced_hill_climbing_sampling=False,
        max_time=15
    )
    traces = random_sampler.traces
    traces.print(wrap="y")
    

from pathlib import Path
from macq.generate.pddl import RandomGoalSampling

if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent

    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    random_sampler = RandomGoalSampling(
        new_domain="new_blocks_dom.pddl",
        new_prob="new_blocks_prob.pddl",
        dom=dom,
        prob=prob,
        num_traces=3,
        steps_deep=10,
        subset_size_perc=0.1,
        enforced_hill_climbing_sampling=False
    )
    traces = random_sampler.traces
    traces.print(wrap="y")
    #TODO: test changing goal
    

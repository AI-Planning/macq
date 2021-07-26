from pathlib import Path
from macq.generate.pddl import RandomGoalSampling

if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent

    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    #TODO: test enforced hill climbing sampling
    random_sampler = RandomGoalSampling(
        dom=dom,
        prob=prob,
        num_traces=3,
        steps_deep=10,
        subset_size_perc=0.1,
        enforced_hill_climbing_sampling=False
    )
    traces = random_sampler.traces
    # traces.print(wrap="y")
    # test changing goal to one of the previous goals generated
    goal = random_sampler.goals[0]
    for f in goal:
        print(f)
    random_sampler.change_goal(goal)
    plan = random_sampler.generate_plan()
    print()
    print(plan)
    

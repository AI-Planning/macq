from pathlib import Path
from macq.generate.pddl import VanillaSampling
from macq.trace import TraceList


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())
    vanilla = VanillaSampling(dom=dom, prob=prob, plan_len=7, num_traces=10)

    plan = vanilla.generate_plan()
    print(plan)
    print()
    # test writing plan to file
    path = str((base / "generated_testing_files/plan.ipc").resolve())
    plan.write_to_file(path)
    # test reading plan from file and using it
    plan = vanilla.generate_plan(from_ipc_file=True, filename=path)
    tracelist = TraceList()
    tracelist.append(vanilla.generate_single_trace_from_plan(plan))
    tracelist.print(wrap="y")
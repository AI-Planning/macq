from pathlib import Path
from macq.generate.pddl import *


def blocks_world(num_traces: int):
    base = Path(__file__).parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    return VanillaSampling(
        dom=dom, prob=prob, plan_len=5, num_traces=num_traces, seed=42
    ).traces

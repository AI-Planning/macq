from macq.extract import Extract, modes
from macq.observation import (
    PartialObservabilityToken,
)
from macq.trace import *
from macq.generate.pddl import VanillaSampling
from pathlib import Path


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = (base / "tests/pddl_testing_files/blocks_domain.pddl").resolve()
    prob = (base / "tests/pddl_testing_files/blocks_problem.pddl").resolve()
    vanilla = VanillaSampling(dom=dom, prob=prob, plan_len=5, num_traces=1)
    traces = vanilla.traces
    print(vanilla.problem.init)
    traces.print(wrap="y")

    observations = traces.tokenize(
        PartialObservabilityToken,
        method=PartialObservabilityToken.random_subset,
        percent_missing=0,
    )
    model = Extract(observations, modes.SLAF)

    print()
    print(model.details())

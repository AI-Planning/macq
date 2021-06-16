from macq.extract import Extract, modes
from macq.observation import (
    PartialObservabilityTokenPropositions,
    PartialObservabilityToken,
)
from macq.trace import *
from tests.utils.realistic_trace import real_trace_list
from macq.generate.pddl import VanillaSampling
from pathlib import Path


if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent.parent
    dom = (base / "tests/pddl_testing_files/blocks_domain.pddl").resolve()
    prob = (base / "tests/pddl_testing_files/blocks_problem.pddl").resolve()
    traces = VanillaSampling(dom=dom, prob=prob, plan_len=5, num_traces=5).traces

    observations = traces.tokenize(
        PartialObservabilityTokenPropositions,
        method=PartialObservabilityToken.random_subset,
        percent_missing=30,
    )
    # traces.print()
    model = Extract(observations, modes.SLAF)
    print(model.details())

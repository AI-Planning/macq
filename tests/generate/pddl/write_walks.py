"""Writes seeded walks and their observations as trace files, into the directory given."""
import sys
from pathlib import Path

from macq.io import write_trace
from macq.observation import NoisyObservation, PartialObservation
from macq.generate.pddl import UniformWalkSampling

FILES = Path(__file__).resolve().parent.parent.parent / "pddl_testing_files"


def write_all(directory) -> None:
    directory = Path(directory)
    sampler = UniformWalkSampling(
        FILES / "walk_domain.pddl", FILES / "walk_problem.pddl", seed=2027, max_actions=8
    )
    for index, trace in enumerate(sampler.iter_traces(6)):
        partial = trace.tokenize(
            PartialObservation,
            percent_missing=0.3,
            rng=sampler.trace_rng(index, "partial"),
        )
        noisy = trace.tokenize(
            NoisyObservation, percent_noisy=0.1, rng=sampler.trace_rng(index, "noisy")
        )
        write_trace(directory / f"{index:04}-walk.json", trace)
        write_trace(directory / f"{index:04}-partial.json", partial)
        write_trace(directory / f"{index:04}-noisy.json", noisy)


if __name__ == "__main__":
    write_all(sys.argv[1])

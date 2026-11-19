"""Prints a canonical text rendering of seeded walks and their observations."""
import sys
from pathlib import Path

from macq.trace import Trace
from macq.observation import NoisyObservation, PartialObservation
from macq.generate.pddl import UniformWalkSampling

FILES = Path(__file__).resolve().parent.parent.parent / "pddl_testing_files"
SYMBOLS = {True: "1", False: "0", None: "?"}


def render_state(state) -> str:
    return "".join(SYMBOLS[state[fluent]] for fluent in state)


def render_action(action) -> str:
    if action is None:
        return "-"
    return " ".join([action.name, *[o.name for o in action.obj_params]])


def render_trace(trace: Trace) -> str:
    return "\n".join(
        f"{step.index} {render_state(step.state)} {render_action(step.action)}"
        for step in trace
    )


def render_all() -> str:
    sampler = UniformWalkSampling(
        FILES / "walk_domain.pddl", FILES / "walk_problem.pddl", seed=2027, max_actions=8
    )
    lines = [" ".join(str(f) for f in sampler.grounded_fluents)]
    for index, trace in enumerate(sampler.iter_traces(6)):
        lines += [f"trace {index}", render_trace(trace)]
        partial = trace.tokenize(
            PartialObservation,
            percent_missing=0.3,
            rng=sampler.trace_rng(index, "partial"),
        )
        noisy = trace.tokenize(
            NoisyObservation, percent_noisy=0.1, rng=sampler.trace_rng(index, "noisy")
        )
        lines += [f"partial {render_state(o.state)}" for o in partial]
        lines += [f"noisy {render_state(o.state)}" for o in noisy]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.stdout.write(render_all())

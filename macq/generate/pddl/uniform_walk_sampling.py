import hashlib
import json
import random
from pathlib import Path
from typing import Iterator, Union

from pddl.core import Domain, Problem

from . import Generator
from ...trace import Step, Trace
from ...utils import InvalidNumberOfTraces, set_plan_length

STREAMS = ("walk", "partial", "noisy")


def trace_rng(
    seed: int, domain: str, problem: str, stream: str, index: int
) -> random.Random:
    """Creates the random generator for one purpose on one trace.

    The same inputs give the same generator on every run, and separate streams let a
    trace's walk stay the same whatever is later hidden or flipped in its states.

    Args:
        seed (int):
            The master seed.
        domain (str):
            The name the domain declares.
        problem (str):
            The name the problem declares.
        stream (str):
            What the generator is for: `walk`, `partial` or `noisy`.
        index (int):
            The index of the trace.

    Returns:
        A random generator independent of the global one.

    Raises:
        TypeError:
            Raised if the seed is not an integer.
        ValueError:
            Raised if the stream is unknown or the index is not a non-negative integer.
    """
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError(f"The seed must be an integer, not {seed!r}.")
    if stream not in STREAMS:
        raise ValueError(f"Unknown stream {stream!r}. Expected one of {STREAMS}.")
    if not isinstance(index, int) or isinstance(index, bool) or index < 0:
        raise ValueError(f"The trace index must be a non-negative integer, not {index!r}.")
    identity = json.dumps([seed, domain, problem, stream, index], separators=(",", ":"))
    digest = hashlib.sha256(identity.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest, "big"))


class UniformWalkSampling(Generator):
    """Uniform Walk Sampler - inherits the base Generator class and its attributes.

    Generates reproducible random walks from the initial state. Each step picks uniformly
    among the applicable ground actions, ignoring the goal. A walk that reaches a state
    with no applicable action stops there and is kept, so `max_actions` is a maximum.

    Every state lists every type-consistent ground atom of the problem, including static
    ones. A trace depends only on the seed, the declared domain and problem names, the
    PDDL itself and the trace's index, and generating one never uses the network.

    Attributes:
        seed (int):
            The master seed.
        max_actions (int):
            The maximum number of actions in a trace.
    """

    def __init__(
        self,
        dom: Union[str, Path, Domain],
        prob: Union[str, Path, Problem],
        seed: int,
        max_actions: int,
    ):
        """Initializes a uniform walk sampler.

        Args:
            dom (str | Path | Domain):
                The domain filename or parsed domain.
            prob (str | Path | Problem):
                The problem filename or parsed problem.
            seed (int):
                The master seed.
            max_actions (int):
                The maximum number of actions in a trace.

        Raises:
            TypeError:
                Raised if the seed is not an integer.
            InvalidPlanLength:
                Raised if `max_actions` is not positive.
        """
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError(f"The seed must be an integer, not {seed!r}.")
        self.seed = seed
        self.max_actions = set_plan_length(max_actions)
        super().__init__(dom=dom, prob=prob, ignore_static_fluents=False)

    def trace_rng(self, index: int, stream: str = "walk") -> random.Random:
        """Creates the random generator for one purpose on one of this sampler's traces.

        Args:
            index (int):
                The index of the trace.
            stream (str):
                What the generator is for: `walk`, `partial` or `noisy`.

        Returns:
            A random generator independent of the global one.
        """
        return trace_rng(
            self.seed,
            str(self.domain.name),
            str(self.problem.name),
            stream,
            index,
        )

    def generate_trace(self, index: int) -> Trace:
        """Generates the trace with the given index.

        Args:
            index (int):
                The index of the trace.

        Returns:
            A trace of up to `max_actions` actions, whose last step has no action.
        """
        rng = self.trace_rng(index)
        trace = Trace()
        state = self.task.initial_state
        for step_index in range(1, self.max_actions + 1):
            applicable = self.task.applicable_actions(state)
            if not applicable:
                break
            action = rng.choice(applicable)
            trace.append(
                Step(self.state_to_macq(state), self.action_to_macq(action), step_index)
            )
            state = self.task.progress(state, action)
        trace.append(Step(self.state_to_macq(state), None, len(trace) + 1))
        return trace

    def iter_traces(self, count: int, start: int = 0) -> Iterator[Trace]:
        """Generates consecutive traces one at a time, keeping none of them.

        Args:
            count (int):
                The number of traces to generate.
            start (int):
                The index of the first trace.

        Returns:
            An iterator over the traces.

        Raises:
            InvalidNumberOfTraces:
                Raised if `count` is negative.
        """
        if count < 0:
            raise InvalidNumberOfTraces()
        return map(self.generate_trace, range(start, start + count))

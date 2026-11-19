import random

import pytest

from macq.core import GroundedFluent, ObjectType, PlanningObject
from macq.trace import State, Step, Trace
from macq.observation import NoisyObservation, PartialObservation


def make_step(index=1):
    objects = [PlanningObject(f"o{i}", ObjectType("object")) for i in range(20)]
    fluents = {GroundedFluent("p", [o]): i % 2 == 0 for i, o in enumerate(objects)}
    return Step(State(fluents), None, index)


def values(observation):
    return [observation.state[f] for f in observation.state]


TOKENS = [
    (PartialObservation, {"percent_missing": 0.5}),
    (NoisyObservation, {"percent_noisy": 0.5}),
    (NoisyObservation, {"percent_noisy": 0.5, "replace": True}),
]


@pytest.mark.parametrize("token,kwargs", TOKENS)
def test_same_rng_seed_gives_the_same_observation(token, kwargs):
    first = token(make_step(), rng=random.Random(7), **kwargs)
    second = token(make_step(), rng=random.Random(7), **kwargs)
    assert values(first) == values(second)


@pytest.mark.parametrize("token,kwargs", TOKENS)
def test_rng_leaves_the_global_generator_alone(token, kwargs):
    random.seed(3)
    before = random.getstate()
    token(make_step(), rng=random.Random(7), **kwargs)
    assert random.getstate() == before


@pytest.mark.parametrize("token,kwargs", TOKENS)
def test_global_generator_stays_the_default(token, kwargs):
    random.seed(11)
    first = token(make_step(), **kwargs)
    random.seed(11)
    second = token(make_step(), **kwargs)
    assert values(first) == values(second)


def test_different_rng_seeds_hide_different_fluents():
    first = PartialObservation(make_step(), percent_missing=0.5, rng=random.Random(1))
    second = PartialObservation(make_step(), percent_missing=0.5, rng=random.Random(2))
    assert values(first) != values(second)


def test_partial_hides_exactly_the_requested_share():
    observation = PartialObservation(
        make_step(), percent_missing=0.25, rng=random.Random(1)
    )
    assert values(observation).count(None) == 5


def test_noisy_flips_exactly_the_requested_share():
    step = make_step()
    original = [step.state[f] for f in step.state]
    observation = NoisyObservation(step, percent_noisy=0.25, rng=random.Random(1))
    flips = sum(a != b for a, b in zip(original, values(observation)))
    assert flips == 5


def test_a_trace_can_be_tokenized_with_its_own_rng():
    trace = Trace([make_step(1), make_step(2)])
    first = trace.tokenize(PartialObservation, percent_missing=0.5, rng=random.Random(5))
    second = trace.tokenize(PartialObservation, percent_missing=0.5, rng=random.Random(5))
    assert [values(o) for o in first] == [values(o) for o in second]
    assert values(first[0]) != values(first[1])

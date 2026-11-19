"""Tokenizing at rate 0 keeps a state's values, including unknowns, exactly."""
import logging
import warnings

import pytest

from macq.trace import Fluent, PartialState, PlanningObject, State, Step
from macq.observation import (
    AtomicPartialObservation,
    IdentityObservation,
    NoisyObservation,
    PartialObservation,
)

OBJECTS = [PlanningObject("object", f"o{i}") for i in range(6)]
VALUES = [True, False, None, True, None, False]


def make_step(partial=True):
    values = VALUES if partial else [bool(v) for v in VALUES]
    fluents = {Fluent("p", [o]): v for o, v in zip(OBJECTS, values)}
    state = PartialState(fluents) if partial else State(fluents)
    return Step(state, None, 1)


def values_by_name(state):
    return {str(f): state[f] for f in state}


TOKENS = [
    (PartialObservation, {"percent_missing": 0}),
    (AtomicPartialObservation, {"percent_missing": 0}),
    (NoisyObservation, {"percent_noisy": 0}),
    (IdentityObservation, {}),
]


@pytest.mark.parametrize("token,kwargs", TOKENS)
def test_rate_zero_keeps_unknowns(token, kwargs):
    step = make_step()
    observation = token(step, **kwargs)
    assert values_by_name(observation.state) == values_by_name(step.state)


@pytest.mark.parametrize("token,kwargs", TOKENS)
def test_rate_zero_does_not_warn(token, kwargs, caplog):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with caplog.at_level(logging.WARNING):
            token(make_step(), **kwargs)
    assert caplog.records == []


@pytest.mark.parametrize("token", [PartialObservation, AtomicPartialObservation])
def test_rate_zero_on_full_state_hides_nothing(token):
    step = make_step(partial=False)
    observation = token(step, percent_missing=0)
    assert values_by_name(observation.state) == values_by_name(step.state)

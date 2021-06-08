import pytest
from macq.model import Model
from tests.extract.extract import generate_observer_model


def test_model_serialization():
    model = generate_observer_model()
    s = model.serialize()
    model2 = Model.deserialize(s)
    assert model2.serialize() == s

import pytest
from macq.extract import Model
from tests.utils.generators import generate_observer_model


# serialization is broken atm
# def test_model_serialization():
#     model = generate_observer_model()
#     s = model.serialize()
#     model2 = Model.deserialize(s)
#     assert model2.serialize() == s

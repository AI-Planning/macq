from macq.extract import *
from tests.utils.test_model import generate_test_model as TestModel


def test_model():
    model = TestModel()
    assert model != "model"
    s = model.serialize("test_model.json")
    assert s
    d = Model.deserialize(s)
    assert d == model

    with open("test_model.json", "r") as f:
        d = f.read()
        assert d == s

from macq.core import DomainModel
from tests.utils.test_model import generate_test_model


def test_extracted_domain_model_round_trips_through_a_file(tmp_path):
    model = generate_test_model()
    path = tmp_path / "model.json"

    text = model.serialize(str(path))

    assert path.read_text() == text
    assert DomainModel.deserialize(text) == model

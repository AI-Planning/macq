import pytest


@pytest.fixture(autouse=True)
def _run_in_a_temporary_directory(tmp_path, monkeypatch):
    """Files that macq writes to the working directory, such as the PDDL from
    change_goal and change_init, land in the test's own directory."""
    monkeypatch.chdir(tmp_path)

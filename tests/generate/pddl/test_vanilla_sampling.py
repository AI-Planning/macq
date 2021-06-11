import pytest
from pathlib import Path
from macq.utils import TraceSearchTimeOut
from macq.generate.pddl import VanillaSampling

# not working on this branch, should work on model-observer
# test the timer wrapper on vanilla trace generation
# def test_timer_vanilla_wrapper():
#     # exit out to the base macq folder so we can get to /tests
#     base = Path(__file__).parent.parent.parent
#     dom = (base / "pddl_testing_files/playlist_domain.pddl").resolve()
#     prob = (base / "pddl_testing_files/playlist_problem.pddl").resolve()

#     with pytest.raises(TraceSearchTimeOut):
#         VanillaSampling(dom=dom, prob=prob, plan_len=10, num_traces=5)

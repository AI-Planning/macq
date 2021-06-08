# test the timer wrapper on vanilla trace generation
# def test_timer_vanilla_wrapper():
#     # exit out to the base macq folder so we can get to /tests
#     base = Path(__file__).parent.parent
#     dom = (base / "tests/pddl_testing_files/playlist_domain.pddl").resolve()
#     prob = (base / "tests/pddl_testing_files/playlist_problem.pddl").resolve()

#     with pytest.raises(TraceSearchTimeOut):
#         VanillaSampling(dom, prob, 10, 5)

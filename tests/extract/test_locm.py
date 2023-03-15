from pathlib import Path
from pprint import pprint
from typing import List

from graphviz import Digraph

from macq.extract import Extract, modes
from macq.extract.locm import AP, LOCM, Hypothesis
from macq.generate.pddl import *
from macq.observation import ActionObservation
from macq.trace import *

EX = 2


def get_fluent(name: str, objs: List[str]):
    objects = [PlanningObject(o.split()[0], o.split()[1]) for o in objs]
    return Fluent(name, objects)


def test_locm():
    base = Path(__file__).parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    traces = TraceList()

    generator = FDRandomWalkSampling(dom=dom, prob=prob)

    print(generator.traces.print())

    observations = traces.tokenize(ActionObservation)

    model = Extract(observations, modes.LOCM, debug=False)

    assert model

    model_blocks_dom = str(
        (base / "pddl_testing_files/model_blocks_domain.pddl").resolve()
    )
    model_blocks_prob = str(
        (base / "pddl_testing_files/model_blocks_problem.pddl").resolve()
    )
    model.to_pddl(
        "model_blocks_dom", "model_blocks_prob", model_blocks_dom, model_blocks_prob
    )


def get_example_obs(print_trace=False):
    objects = {
        "c1": PlanningObject("container", "c1"),
        "c2": PlanningObject("container", "c2"),
        "c3": PlanningObject("container", "c3"),
        "j1": PlanningObject("jack", "j1"),
        "j2": PlanningObject("jack", "j2"),
        "wr1": PlanningObject("wrench", "wr1"),
        "wr2": PlanningObject("wrench", "wr2"),
    }
    fluents = {
        "open1": Fluent("open", [objects["c1"]]),
        "open2": Fluent("open", [objects["c2"]]),
        "open3": Fluent("open", [objects["c3"]]),
        "j1in": Fluent("in", [objects["j1"], objects["c1"]]),
        "j2in": Fluent("in", [objects["j2"], objects["c2"]]),
        "wr1in": Fluent("in", [objects["wr1"], objects["c1"]]),
        "wr2in": Fluent("in", [objects["wr2"], objects["c2"]]),
    }
    actions = {
        "open1": Action("open", [objects["c1"]]),
        "open2": Action("open", [objects["c2"]]),
        "open3": Action("open", [objects["c3"]]),
        "close1": Action("close", [objects["c1"]]),
        "close2": Action("close", [objects["c2"]]),
        "close3": Action("close", [objects["c3"]]),
        "fetchj1": Action("fetch_jack", [objects["j1"], objects["c1"]]),
        "fetchj2": Action("fetch_jack", [objects["j2"], objects["c2"]]),
        "putj1": Action("putaway_jack", [objects["j1"], objects["c1"]]),
        "putj2": Action("putaway_jack", [objects["j2"], objects["c2"]]),
        "fetchwr1": Action("fetch_wrench", [objects["wr1"], objects["c1"]]),
        "fetchwr2": Action("fetch_wrench", [objects["wr2"], objects["c2"]]),
        "putwr1": Action("putaway_wrench", [objects["wr1"], objects["c1"]]),
        "putwr2": Action("putaway_wrench", [objects["wr2"], objects["c2"]]),
        "closewr": Action("close", [objects["wr1"]]),
    }

    if EX == 1:
        # open(c1); fetch jack(j1,c1); fetch wrench(wr1,c1); close(c1);
        # open(c2); fetch wrench(wr2,c2); fetch jack(j2,c2); close(c2);
        # open(c3); close(c3)
        states_true = [
            ["open3", "j1in", "j2in", "wr1in", "wr2in"],
            ["open3", "open1", "j1in", "j2in", "wr1in", "wr2in"],
            ["open3", "open1", "j2in", "wr1in", "wr2in"],
            ["open3", "open1", "j2in", "wr2in"],
            ["open3", "j2in", "wr2in"],
            ["open3", "open2", "j2in", "wr2in"],
            ["open3", "open2", "j2in"],
            ["open3", "open2"],
            ["open3"],
            [],
            ["open3"],
        ]
        states = [
            State({fluent: name in state_true for name, fluent in fluents.items()})
            for state_true in states_true
        ]
        traces = TraceList(
            [
                Trace(
                    [
                        Step(states[0], actions["open1"], 1),
                        Step(states[1], actions["fetchj1"], 2),
                        Step(states[2], actions["fetchwr1"], 3),
                        Step(states[3], actions["close1"], 4),
                        Step(states[4], actions["open2"], 5),
                        Step(states[5], actions["fetchwr2"], 6),
                        Step(states[6], actions["fetchj2"], 7),
                        Step(states[7], actions["close2"], 8),
                        Step(states[9], actions["close3"], 9),
                        Step(states[8], actions["open3"], 10),
                        Step(states[10], None, 11),
                        # Step(states[10], actions["closewr"], 11),
                        # Step(states[11], None, 12),
                    ]
                ),
            ]
        )
    else:
        # open(c1); putaway jack(j1,c1); close(c1); open(c2); putaway jack(j2,c2);
        # open(c1); fetch jack(j1,c1); fetch wrench(wr1,c1);
        # fetch jack(j2,c2); close(c1);
        states_true = [
            ["wr1in", "wr2in"],
            ["open1", "wr1in", "wr2in"],
            ["open1", "wr1in", "wr2in", "j1in"],
            ["wr1in", "wr2in", "j1in"],
            ["open2", "wr1in", "wr2in", "j1in"],
            ["open2", "wr1in", "wr2in", "j1in", "j2in"],
            ["open1", "open2", "wr1in", "wr2in", "j1in", "j2in"],
            ["open1", "open2", "wr1in", "wr2in", "j2in"],
            ["open1", "open2", "wr2in", "j2in"],
            ["open1", "open2", "wr2in"],
            ["open2", "wr2in"],
        ]
        states = [
            State({fluent: name in state_true for name, fluent in fluents.items()})
            for state_true in states_true
        ]
        traces = TraceList(
            [
                Trace(
                    [
                        Step(states[0], actions["open1"], 1),
                        Step(states[1], actions["putj1"], 2),
                        Step(states[2], actions["close1"], 3),
                        Step(states[3], actions["open2"], 4),
                        Step(states[4], actions["putj2"], 5),
                        Step(states[5], actions["open1"], 6),
                        Step(states[6], actions["fetchj1"], 7),
                        Step(states[7], actions["fetchwr1"], 8),
                        Step(states[8], actions["fetchj2"], 9),
                        Step(states[9], actions["close1"], 10),
                    ]
                ),
            ]
        )

    if print_trace:
        # traces.print()
        traces.print("color")

    obs = traces.tokenize(ActionObservation)
    return obs


def test_locm_get_sorts(is_test=True):
    from pprint import pprint

    obs = get_example_obs(is_test)
    sorts = LOCM._get_sorts(obs[0])

    if is_test:
        print()
        print("sorts:")
        pprint(sorts)
        print()
    else:
        return sorts


def test_locm_step1(is_test=True):
    obs = get_example_obs(False)
    sorts = test_locm_get_sorts(False)
    ts, ap_state_pointers, os = LOCM._step1(obs[0], sorts)  # type: ignore

    if is_test:
        print("state pointers:")
        pprint(ap_state_pointers)
        print("ts:")
        pprint(ts)
        print()
        print("os:")
        pprint(os)
    else:
        return ts, ap_state_pointers, os


def test_locm_viz():
    _, ap_state_pointers, OS = test_locm_step1(False)  # type: ignore
    state_machines: List[Digraph] = LOCM.viz_state_machines(ap_state_pointers, OS)
    for sm in state_machines:
        sm.render(view=True)


def test_locm_step3(is_test=True):
    sorts = test_locm_get_sorts(False)
    TS, ap_state_pointers, OS = test_locm_step1(False)  # type: ignore
    HS = LOCM._step3(TS, ap_state_pointers, OS, sorts)  # type: ignore
    if is_test:
        print("HS:")
        pprint(HS)
    else:
        return HS


def test_locm_step4(HS=None, is_test=True):
    if HS is None:
        HS = {
            1: {
                1: {
                    Hypothesis(
                        S=1,
                        B=AP(
                            Action(
                                "do_up",
                                [
                                    PlanningObject("nut", "nut1"),
                                    PlanningObject("hub", "hub1"),
                                ],
                            ),
                            1,
                        ),
                        k=1,
                        k_=2,
                        C=AP(
                            Action(
                                "tighten",
                                [
                                    PlanningObject("nut", "nut1"),
                                    PlanningObject("hub", "hub1"),
                                ],
                            ),
                            1,
                        ),
                        l=1,
                        l_=2,
                        G=1,
                        G_=2,
                    ),
                    Hypothesis(
                        S=1,
                        B=AP(
                            Action(
                                "do_up",
                                [
                                    PlanningObject("nut", "nut1"),
                                    PlanningObject("hub", "hub1"),
                                ],
                            ),
                            1,
                        ),
                        k=1,
                        k_=2,
                        C=AP(
                            Action(
                                "undo",
                                [
                                    PlanningObject("nut", "nut1"),
                                    PlanningObject("hub", "hub1"),
                                ],
                            ),
                            1,
                        ),
                        l=1,
                        l_=2,
                        G=1,
                        G_=2,
                    ),
                    Hypothesis(
                        S=1,
                        B=AP(
                            Action(
                                "loosen",
                                [
                                    PlanningObject("nut", "nut1"),
                                    PlanningObject("hub", "hub1"),
                                ],
                            ),
                            1,
                        ),
                        k=1,
                        k_=2,
                        C=AP(
                            Action(
                                "tighten",
                                [
                                    PlanningObject("nut", "nut1"),
                                    PlanningObject("hub", "hub1"),
                                ],
                            ),
                            1,
                        ),
                        l=1,
                        l_=2,
                        G=1,
                        G_=2,
                    ),
                    Hypothesis(
                        S=1,
                        B=AP(
                            Action(
                                "loosen",
                                [
                                    PlanningObject("nut", "nut1"),
                                    PlanningObject("hub", "hub1"),
                                ],
                            ),
                            1,
                        ),
                        k=1,
                        k_=2,
                        C=AP(
                            Action(
                                "undo",
                                [
                                    PlanningObject("nut", "nut1"),
                                    PlanningObject("hub", "hub1"),
                                ],
                            ),
                            1,
                        ),
                        l=1,
                        l_=2,
                        G=1,
                        G_=2,
                    ),
                }
            }
        }
    bindings, param_pointers, params = LOCM._step4(HS)

    if is_test:
        print("bindings:")
        pprint(bindings)
        print("param_pointers:")
        pprint(param_pointers)
        print("params:")
        pprint(params)
    else:
        return bindings, param_pointers, params


def test_locm_step5(is_test=True):
    HS = {
        2: {
            1: {
                Hypothesis(
                    S=1,
                    B=AP(
                        Action(
                            "do_up",
                            [
                                PlanningObject("nut", "nut1"),
                                PlanningObject("hub", "hub1"),
                            ],
                        ),
                        2,
                    ),
                    k=2,
                    k_=1,
                    C=AP(
                        Action(
                            "undo",
                            [
                                PlanningObject("nut", "nut1"),
                                PlanningObject("hub", "hub1"),
                            ],
                        ),
                        2,
                    ),
                    l=2,
                    l_=1,
                    G=2,
                    G_=1,
                ),
                Hypothesis(
                    S=1,
                    B=AP(
                        Action(
                            "jack_up",
                            [
                                PlanningObject("jack", "jack1"),
                                PlanningObject("hub", "hub1"),
                            ],
                        ),
                        2,
                    ),
                    k=2,
                    k_=1,
                    C=AP(
                        Action(
                            "jack_down",
                            [
                                PlanningObject("jack", "jack1"),
                                PlanningObject("hub", "hub1"),
                            ],
                        ),
                        2,
                    ),
                    l=2,
                    l_=1,
                    G=2,
                    G_=3,
                ),
            }
        }
    }

    bindings, param_pointers, params = test_locm_step4(HS, False)  # type: ignore

    print("HS before:")
    pprint(HS)

    HS = LOCM._step5(HS, bindings, param_pointers, params)

    print("HS after:")
    pprint(HS)


if __name__ == "__main__":
    # test_locm_get_sorts()
    # test_locm_step1()
    # test_locm_viz()
    # test_locm_step3()
    # test_locm_step4()
    test_locm_step5()

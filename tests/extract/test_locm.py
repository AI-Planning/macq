from pathlib import Path
from typing import List
from macq.extract.locm import LOCM
from macq.trace import *
from macq.extract import Extract, modes
from macq.observation import ActionObservation
from macq.generate.pddl import *


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
    # open(c1); fetchjack(j,c1); fetchwrench(wr1,c1); close(c1);
    objects = {
        "c": PlanningObject("container", "c1"),
        "j": PlanningObject("jack", "j1"),
        "w": PlanningObject("wrench", "w1"),
    }
    fluents = {
        "open": Fluent("open", [objects["c"]]),
        "jin": Fluent("in c", [objects["j"], objects["c"]]),
        "win": Fluent("in c", [objects["w"], objects["c"]]),
    }
    actions = {
        "open": Action("open", [objects["c"]]),
        "fetchj": Action("fetch_jack", [objects["j"], objects["c"]]),
        "fetchw": Action("fetch_wrench", [objects["w"], objects["c"]]),
        "close": Action("close", [objects["c"]]),
    }
    states = [
        State({fluents["open"]: False, fluents["jin"]: True, fluents["win"]: True}),
        State({fluents["open"]: True, fluents["jin"]: True, fluents["win"]: True}),
        State({fluents["open"]: True, fluents["jin"]: False, fluents["win"]: True}),
        State({fluents["open"]: True, fluents["jin"]: False, fluents["win"]: False}),
        State({fluents["open"]: False, fluents["jin"]: False, fluents["win"]: False}),
    ]
    traces = TraceList(
        [
            Trace(
                [
                    Step(states[0], actions["open"], 1),
                    Step(states[1], actions["fetchj"], 2),
                    Step(states[2], actions["fetchw"], 3),
                    Step(states[3], actions["close"], 4),
                    Step(states[4], None, 5),
                ]
            ),
        ]
    )

    if print_trace:
        traces.print()

    obs = traces.tokenize(ActionObservation)[0]
    return obs


def test_locm_phase1():
    obs = get_example_obs(True)
    phase1 = LOCM._phase1(obs)
    print(phase1)


if __name__ == "__main__":
    test_locm_phase1()

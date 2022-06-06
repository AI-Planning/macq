from pathlib import Path
from typing import List
from macq.trace import *
from macq.extract import Extract, modes
from macq.observation import PartialObservation
from macq.generate.pddl import *


def get_fluent(name: str, objs: List[str]):
    objects = [PlanningObject(o.split()[0], o.split()[1]) for o in objs]
    return Fluent(name, objects)


def test_arms():
    base = Path(__file__).parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    traces = TraceList()
    generator = TraceFromGoal(dom=dom, prob=prob)

    generator.change_goal(
        {
            get_fluent("on", ["object a", "object b"]),
            get_fluent("on", ["object b", "object c"]),
        }
    )
    traces.append(generator.generate_trace())
    generator.change_goal(
        {
            get_fluent("on", ["object b", "object a"]),
            get_fluent("on", ["object c", "object b"]),
        }
    )
    traces.append(generator.generate_trace())

    observations = traces.tokenize(PartialObservation, percent_missing=0.5)
    model = Extract(
        observations,
        modes.ARMS,
        debug=False,
        upper_bound=2,
        min_support=2,
        action_weight=110,
        info_weight=100,
        threshold=0.6,
        info3_default=30,
        plan_default=30,
    )

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
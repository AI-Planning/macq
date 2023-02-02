from pathlib import Path
from typing import List
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

    observations = traces.tokenize(ActionObservation, percent_missing=0.5)

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


if __name__ == "__main__":
    test_locm()

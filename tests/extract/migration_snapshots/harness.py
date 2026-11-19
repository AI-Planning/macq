"""Captures what each extractor learns, so the move of `macq.trace` onto `macq.core` can be checked.

Temporary: this package is deleted when the move finishes. AMDN and ARMS vary between runs even with
every seed fixed, so their MAX-SAT solutions are recorded once and replayed. A learned domain model is
compared through its serialized form, which is lossless and deterministic.

Usage: python harness.py {record,replay} SCENARIO OUTPUT_JSON
"""

import json
import random
import sys
import warnings
from pathlib import Path

from nnf import Aux

HERE = Path(__file__).parent
PDDL = HERE.parent.parent / "pddl_testing_files"
SOLUTIONS = HERE / "solver_solutions"


def _blocks(plan_len, num_traces, **kwargs):
    from macq.generate.pddl import VanillaSampling

    return VanillaSampling(
        dom=str(PDDL / "blocks_domain.pddl"),
        prob=str(PDDL / "blocks_problem.pddl"),
        plan_len=plan_len,
        num_traces=num_traces,
        seed=42,
        **kwargs,
    ).traces


def _deliver(count, max_actions):
    from macq.generate.pddl import UniformWalkSampling
    from macq.trace import TraceList

    sampler = UniformWalkSampling(
        PDDL / "deliver_domain.pddl", PDDL / "deliver_problem.pddl", seed=8, max_actions=max_actions
    )
    return TraceList(list(sampler.iter_traces(count)))


def _action(name, params, objects):
    """Builds a trace action over objects of type `object`, in whatever form `macq.trace` uses."""
    from macq.trace import Action, PlanningObject

    return Action(name, [objects.setdefault(p, PlanningObject("object", p)) for p in params])


def _action_traces(sequence):
    from macq.trace import State, Step, Trace, TraceList

    objects = {}
    steps = []
    for index, (name, *params) in enumerate(sequence):
        steps.append(Step(State(), _action(name, params, objects), index + 1))
    steps.append(Step(State(), None, len(sequence) + 1))
    return TraceList([Trace(steps)])


GRIPPER = [
    ("pick", "b1", "r1"),
    ("move", "r1", "r2"),
    ("drop", "b1", "r2"),
    ("move", "r2", "r1"),
    ("pick", "b2", "r1"),
    ("move", "r1", "r2"),
    ("drop", "b2", "r2"),
    ("pick", "b1", "r2"),
    ("move", "r2", "r1"),
    ("drop", "b1", "r1"),
]
ZERO = [("noop",), ("open", "d1"), ("noop",), ("close", "d1"), ("noop",), ("open", "d2"), ("close", "d2")]
PICK_DROP = [("pick", "b1", "r1"), ("drop", "b1", "r1"), ("pick", "b2", "r1"), ("drop", "b2", "r1")]


def _observer(traces):
    from macq.extract import Extract, modes
    from macq.observation import IdentityObservation

    return Extract(traces.tokenize(IdentityObservation), modes.OBSERVER)


def _slaf(traces):
    from macq.extract import Extract, modes
    from macq.observation import AtomicPartialObservation

    return Extract(traces.tokenize(AtomicPartialObservation, percent_missing=0.1), modes.SLAF)


def _amdn():
    from macq.extract import Extract, modes
    from macq.observation import NoisyPartialDisorderedParallelObservation
    from macq.trace.disordered_parallel_actions_observation_lists import (
        DisorderedParallelActionsObservationLists,
        default_theta_vec,
        num_parameters_feature,
        objects_shared_feature,
    )

    observations = _blocks(5, 1, observe_pres_effs=True).tokenize(
        Token=NoisyPartialDisorderedParallelObservation,
        ObsLists=DisorderedParallelActionsObservationLists,
        features=[objects_shared_feature, num_parameters_feature],
        learned_theta=default_theta_vec(2),
        percent_missing=0,
        percent_noisy=0,
        replace=True,
    )
    return Extract(observations, modes.AMDN, debug=False, occ_threshold=2)


def _arms():
    from macq.extract import Extract, modes
    from macq.observation import PartialObservation

    return Extract(
        _blocks(10, 3).tokenize(PartialObservation, percent_missing=0.3),
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


def _locm(traces, **kwargs):
    from macq.extract import Extract, modes
    from macq.observation import ActionObservation

    return Extract(traces.tokenize(ActionObservation), modes.LOCM, **kwargs)


SCENARIOS = {
    "observer": lambda: _observer(_blocks(8, 3)),
    "observer_deliver": lambda: _observer(_deliver(4, 12)),
    "slaf": lambda: _slaf(_blocks(2, 1)),
    "slaf_deliver": lambda: _slaf(_deliver(1, 2)),
    "amdn": _amdn,
    "arms": _arms,
    "locm_blocks": lambda: _locm(_blocks(30, 1)),
    "locm_deliver": lambda: _locm(_deliver(3, 30)),
    "locm_gripper": lambda: _locm(_action_traces(GRIPPER)),
    "locm_zero": lambda: _locm(_action_traces(ZERO)),
    "locm_statics": lambda: _locm(_action_traces(PICK_DROP), statics={"pick": [("next", 2, 1)]}),
}


def _record_solutions(scenario, solutions):
    import macq.extract.amdn as amdn_module
    from macq.extract.arms import ARMS

    if scenario == "amdn":
        solve = amdn_module.extract_raw_model

        def recording(*args):
            model = solve(*args)
            solutions.append([[str(k), v] for k, v in model.items() if v and not isinstance(k, Aux)])
            return model

        amdn_module.extract_raw_model = recording
    elif scenario == "arms":
        solve = ARMS.step4

        def recording(*args):
            model = solve(*args)
            solutions.append([[str(k), v] for k, v in model.items()])
            return model

        ARMS.step4 = staticmethod(recording)


def _replay_solutions(scenario, solutions):
    import macq.extract.amdn as amdn_module
    from macq.extract.arms import ARMS

    remaining = iter(solutions)
    if scenario == "amdn":
        amdn_module.AMDN._solve_constraints = staticmethod(lambda *args: (None, None))
        amdn_module.extract_raw_model = lambda *args: dict(next(remaining))
    elif scenario == "arms":
        ARMS.step3 = staticmethod(lambda *args: (None, None))
        ARMS.step4 = staticmethod(lambda *args: dict(next(remaining)))


def main(mode, scenario, output):
    warnings.simplefilter("ignore")
    random.seed(1)
    solution_file = SOLUTIONS / f"{scenario}.json"
    solutions = []
    if mode == "record":
        _record_solutions(scenario, solutions)
    elif solution_file.exists():
        _replay_solutions(scenario, json.loads(solution_file.read_text()))

    learned = json.loads(SCENARIOS[scenario]().serialize())

    if mode == "record" and solutions:
        SOLUTIONS.mkdir(exist_ok=True)
        solution_file.write_text(json.dumps(solutions, indent=0) + "\n")
    Path(output).write_text(json.dumps(learned, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:])

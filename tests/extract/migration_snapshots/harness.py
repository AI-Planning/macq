"""Captures what each extractor learns, so the move onto `macq.core` can be checked.

Temporary: this package is deleted when the migration finishes. AMDN and ARMS vary between runs even with
every seed fixed, so their MAX-SAT solutions are recorded once and replayed.

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


def _action_traces(sequence):
    from macq.trace import Action, PlanningObject, State, Step, Trace, TraceList

    objects = {}
    steps = []
    for index, (name, *params) in enumerate(sequence):
        action = Action(name, [objects.setdefault(p, PlanningObject("object", p)) for p in params])
        steps.append(Step(State(), action, index + 1))
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


def _observer():
    from macq.extract import Extract, modes
    from macq.observation import IdentityObservation

    return Extract(_blocks(8, 3).tokenize(IdentityObservation), modes.OBSERVER)


def _slaf():
    from macq.extract import Extract, modes
    from macq.observation import AtomicPartialObservation

    return Extract(_blocks(2, 1).tokenize(AtomicPartialObservation, percent_missing=0.1), modes.SLAF)


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
    "observer": _observer,
    "slaf": _slaf,
    "amdn": _amdn,
    "arms": _arms,
    "locm_blocks": lambda: _locm(_blocks(30, 1)),
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


def _sort_key(value):
    return json.dumps(value, sort_keys=True)


def _legacy_fluent(fluent):
    if hasattr(fluent, "param_act_inds"):
        return [fluent.name, list(fluent.param_sorts), list(fluent.param_act_inds)]
    return str(fluent).replace(" )", ")")


def _unique_sorted(values):
    return sorted({_sort_key(v): v for v in values}.values(), key=_sort_key)


_CORE_PARTS = {"precond": "positive_preconditions", "add": "add_effects", "delete": "delete_effects"}


def _action_part(action, part):
    return getattr(action, _CORE_PARTS[part] if hasattr(action, "add_effects") else part)


def _normalize_lifted(model, scenario):
    declared = {f.name: [str(p.object_type) for p in f.parameters] for f in model.fluents}

    def fluent(bound):
        types = declared[bound.name]
        if scenario == "arms":  # the old output had no bindings to compare
            return "(" + " ".join([bound.name, *types]) + ")"
        return [bound.name, types, list(bound.bounded_params)]

    actions = {}
    for action in model.actions:
        signature = " ".join([action.name, *(str(p.object_type) for p in action.params)])
        actions[f"({signature})"] = {
            part: _unique_sorted(fluent(f) for f in _action_part(action, part)) for part in _CORE_PARTS
        }
    used = [f for action in actions.values() for part in action.values() for f in part]
    return {"fluents": _unique_sorted(used), "actions": dict(sorted(actions.items()))}


def normalize(model, scenario):
    """Returns the learned content of a domain model in a canonical, comparable form."""
    if getattr(getattr(model, "form", None), "value", None) == "lifted":
        return _normalize_lifted(model, scenario)
    actions = {}
    for action in model.actions:
        actions[action.details().replace(" )", ")")] = {
            part: _unique_sorted(_legacy_fluent(f) for f in _action_part(action, part))
            for part in _CORE_PARTS
        }
    return {
        "fluents": _unique_sorted(_legacy_fluent(f) for f in model.fluents),
        "actions": dict(sorted(actions.items())),
    }


def main(mode, scenario, output):
    warnings.simplefilter("ignore")
    random.seed(1)
    solution_file = SOLUTIONS / f"{scenario}.json"
    solutions = []
    if mode == "record":
        _record_solutions(scenario, solutions)
    elif solution_file.exists():
        _replay_solutions(scenario, json.loads(solution_file.read_text()))

    result = normalize(SCENARIOS[scenario](), scenario)

    if mode == "record" and solutions:
        SOLUTIONS.mkdir(exist_ok=True)
        solution_file.write_text(json.dumps(solutions, indent=0) + "\n")
    Path(output).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main(*sys.argv[1:])

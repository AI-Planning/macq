from macq.trace.disordered_parallel_actions_observation_lists import (
    default_theta_vec,
    num_parameters_feature,
    objects_shared_feature,
)
from macq.utils.tokenization_errors import TokenizationError
from tests.utils.generators import generate_blocks_traces
from macq.extract import Extract, modes
from macq.generate.pddl import *
from macq.observation import *
from macq.trace import *
from pathlib import Path
import pytest


def test_tokenization_error():
    with pytest.raises(TokenizationError):
        traces = generate_blocks_traces(3)
        assert traces, "Failed to generate traces for tokenization error test."
        trace = traces[0]
        trace.tokenize(Token=NoisyPartialDisorderedParallelObservation)


def gen_tracelist():
    # define objects
    red_truck = PlanningObject("", "red_truck")
    blue_truck = PlanningObject("", "blue_truck")
    location_a = PlanningObject("", "location_a")
    location_b = PlanningObject("", "location_b")
    location_c = PlanningObject("", "location_c")
    location_d = PlanningObject("", "location_d")

    red_truck_is_truck = Fluent("truck", [red_truck])
    blue_truck_is_truck = Fluent("truck", [blue_truck])
    location_a_is_place = Fluent("place", [location_a])
    location_b_is_place = Fluent("place", [location_b])
    location_c_is_place = Fluent("place", [location_c])
    location_d_is_place = Fluent("place", [location_d])
    red_at_a = Fluent("at", [red_truck, location_a])
    red_at_b = Fluent("at", [red_truck, location_b])
    red_at_c = Fluent("at", [red_truck, location_c])
    red_at_d = Fluent("at", [red_truck, location_d])
    blue_at_a = Fluent("at", [blue_truck, location_a])
    blue_at_b = Fluent("at", [blue_truck, location_b])
    blue_at_c = Fluent("at", [blue_truck, location_c])
    blue_at_d = Fluent("at", [blue_truck, location_d])

    drive_red_a_b = Action(
        "drive",
        [red_truck, location_a, location_b],
        precond={
            red_truck_is_truck,
            location_a_is_place,
            location_b_is_place,
            red_at_a,
        },
        add={red_at_b},
        delete={red_at_a},
    )
    drive_blue_c_d = Action(
        "drive",
        [blue_truck, location_c, location_d],
        precond={
            blue_truck_is_truck,
            location_c_is_place,
            location_d_is_place,
            blue_at_c,
        },
        add={blue_at_d},
        delete={blue_at_c},
    )
    drive_blue_d_b = Action(
        "drive",
        [blue_truck, location_d, location_b],
        precond={
            blue_truck_is_truck,
            location_d_is_place,
            location_b_is_place,
            blue_at_d,
        },
        add={blue_at_b},
        delete={blue_at_d},
    )
    drive_red_b_d = Action(
        "drive",
        [red_truck, location_b, location_d],
        precond={
            red_truck_is_truck,
            location_b_is_place,
            location_d_is_place,
            red_at_b,
        },
        add={red_at_d},
        delete={red_at_b},
    )

    # trace:  {red a -> b, blue c -> d}, {blue d -> b}, {red b -> d}, {red d -> a, blue b -> c}
    step_0 = Step(
        State(
            {
                red_truck_is_truck: True,
                blue_truck_is_truck: True,
                location_a_is_place: True,
                location_b_is_place: True,
                location_c_is_place: True,
                location_d_is_place: True,
                red_at_a: True,
                red_at_b: False,
                red_at_c: False,
                red_at_d: False,
                blue_at_a: False,
                blue_at_b: False,
                blue_at_c: True,
                blue_at_d: False,
            }
        ),
        drive_red_a_b,
        0,
    )

    step_1 = Step(
        State(
            {
                red_truck_is_truck: True,
                blue_truck_is_truck: True,
                location_a_is_place: True,
                location_b_is_place: True,
                location_c_is_place: True,
                location_d_is_place: True,
                red_at_a: False,
                red_at_b: True,
                red_at_c: False,
                red_at_d: False,
                blue_at_a: False,
                blue_at_b: False,
                blue_at_c: True,
                blue_at_d: False,
            }
        ),
        drive_blue_c_d,
        1,
    )

    step_2 = Step(
        State(
            {
                red_truck_is_truck: True,
                blue_truck_is_truck: True,
                location_a_is_place: True,
                location_b_is_place: True,
                location_c_is_place: True,
                location_d_is_place: True,
                red_at_a: False,
                red_at_b: True,
                red_at_c: False,
                red_at_d: False,
                blue_at_a: False,
                blue_at_b: False,
                blue_at_c: False,
                blue_at_d: True,
            }
        ),
        drive_blue_d_b,
        2,
    )

    step_3 = Step(
        State(
            {
                red_truck_is_truck: True,
                blue_truck_is_truck: True,
                location_a_is_place: True,
                location_b_is_place: True,
                location_c_is_place: True,
                location_d_is_place: True,
                red_at_a: False,
                red_at_b: True,
                red_at_c: False,
                red_at_d: False,
                blue_at_a: False,
                blue_at_b: True,
                blue_at_c: False,
                blue_at_d: False,
            }
        ),
        drive_red_b_d,
        3,
    )

    step_4 = Step(
        State(
            {
                red_truck_is_truck: True,
                blue_truck_is_truck: True,
                location_a_is_place: True,
                location_b_is_place: True,
                location_c_is_place: True,
                location_d_is_place: True,
                red_at_a: False,
                red_at_b: False,
                red_at_c: False,
                red_at_d: True,
                blue_at_a: False,
                blue_at_b: True,
                blue_at_c: False,
                blue_at_d: False,
            }
        ),
        None,
        4,
    )
    # step_2.action = None
    # return TraceList([Trace([step_0, step_1, step_2])])#, step_3, step_4])])
    return TraceList([Trace([step_0, step_1, step_2, step_3, step_4])])

def test_amdn():
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent

    # use blocksworld (NOTE: no actions are parallel in this domain)
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())
    # TODO: replace with a domain-specific random trace generator
    traces = RandomGoalSampling(
        prob=prob,
        dom=dom,
        observe_pres_effs=True,
        num_traces=1,
        steps_deep=4,
        subset_size_perc=0.1,
        enforced_hill_climbing_sampling=True,
    ).traces

    # use the simple truck domain for debugging
    # traces = gen_tracelist()

    # use the simple door domain for debugging
    # dom = str((base / "pddl_testing_files/door_dom.pddl").resolve())
    # prob = str((base / "pddl_testing_files/door_prob.pddl").resolve())
    # traces = TraceList([TraceFromGoal(dom=dom, prob=prob, observe_pres_effs=True).trace])

    traces.print(wrap="y")

    features = [objects_shared_feature, num_parameters_feature]
    learned_theta = default_theta_vec(2)
    observations = traces.tokenize(
        Token=NoisyPartialDisorderedParallelObservation,
        ObsLists=DisorderedParallelActionsObservationLists,
        features=features,
        learned_theta=learned_theta,
        percent_missing=0,
        percent_noisy=0,
        replace=True,
    )
    model = Extract(observations, modes.AMDN, debug=False, occ_threshold=2)
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

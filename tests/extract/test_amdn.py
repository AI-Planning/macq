from macq.trace.disordered_parallel_actions_observation_lists import default_theta_vec, num_parameters_feature, objects_shared_feature
from macq.utils.tokenization_errors import TokenizationError
from tests.utils.generators import generate_blocks_traces
from macq.extract import Extract, modes
from macq.generate.pddl import RandomGoalSampling, Generator
from macq.observation import *
from macq.trace import *
from pathlib import Path
import pytest

def test_tokenization_error():
    with pytest.raises(TokenizationError):
        trace = generate_blocks_traces(3)[0]
        trace.tokenize(Token=NoisyPartialDisorderedParallelObservation)

def test_tracelist():
    # define objects
    red_truck = PlanningObject("object", "red_truck")
    blue_truck = PlanningObject("object", "blue_truck")
    location_a = PlanningObject("object", "location_a")
    location_b = PlanningObject("object", "location_b")
    location_c = PlanningObject("object", "location_c")
    location_d = PlanningObject("object", "location_d")

    red_truck_is_truck = Fluent("truck", [red_truck])
    blue_truck_is_truck = Fluent("truck", [blue_truck])
    location_a_is_place = Fluent("place", [location_a])
    location_b_is_place = Fluent("place", [location_b])
    location_c_is_place = Fluent("place", [location_c])
    location_d_is_place = Fluent("place", [location_d])
    red_at_a = Fluent("at", [red_truck, location_a])
    red_at_b = Fluent("at", [red_truck, location_b])
    blue_at_c = Fluent("at", [blue_truck, location_c])
    blue_at_d = Fluent("at", [blue_truck, location_d])    
    blue_at_a = Fluent("at", [blue_truck, location_a])
    blue_at_b = Fluent("at", [blue_truck, location_b])

    drive_red_a_b = Action("drive", [red_truck, location_a, location_b], precond={red_truck_is_truck, location_a_is_place, location_b_is_place, red_at_a}, add={red_at_b}, delete={red_at_a})
    drive_blue_c_d = Action("drive", [blue_truck, location_c, location_d], precond={blue_truck_is_truck, location_c_is_place, location_d_is_place, blue_at_c}, add={blue_at_d}, delete={blue_at_c})


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
                blue_at_c: True, 
                blue_at_d: False, 
            }),
            drive_red_a_b,
            0
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
                blue_at_c: True, 
                blue_at_d: False, 
            }),
            drive_blue_c_d,
            1
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
                blue_at_c: False, 
                blue_at_d: True, 
            }),
            None,
            2
            )
        
    test_trace_1 = Trace([step_0, step_1, step_2])
    return TraceList([test_trace_1])

if __name__ == "__main__":
    # exit out to the base macq folder so we can get to /tests
    base = Path(__file__).parent.parent
    dom = str((base / "pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "pddl_testing_files/blocks_problem.pddl").resolve())

    traces = test_tracelist()

    """
    # TODO: replace with a domain-specific random trace generator
    traces = RandomGoalSampling(
        # prob=prob,
        # dom=dom,
        problem_id=2337,
        observe_pres_effs=True,
        num_traces=1,
        steps_deep=50,
        subset_size_perc=0.1,
        enforced_hill_climbing_sampling=True
    ).traces
    traces.print()
    """
    

    features = [objects_shared_feature, num_parameters_feature]
    learned_theta = default_theta_vec(2)
    observations = traces.tokenize(
        Token=NoisyPartialDisorderedParallelObservation,
        ObsLists=DisorderedParallelActionsObservationLists,
        features=features,
        learned_theta=learned_theta,
        percent_missing=0,
        percent_noisy=0,
    )
    model = Extract(observations, modes.AMDN, occ_threshold = 3)
    f = open("results.txt", "w")
    f.write(model.details())

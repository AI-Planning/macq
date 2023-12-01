from pathlib import Path
from unittest import TestCase

from macq.trace import Fluent, PlanningObject, TraceList, Trace
from macq.generate.pddl import TraceFromGoal
from macq.extract import LearnedLiftedFluent, LearnedLiftedAction, Model, LOCM, sam
from  macq.observation import ObservedTraceList, ActionObservation



# !!!note to self: need to change goal fluents to the original goal(even if it set automatically)
# because an error accuses

def get_fluent(name: str, objs: list[str]):
    objects = [PlanningObject(o.split()[0], o.split()[1])
               for o in objs]
    return Fluent(name, objects)


def make_log_model():
    lift_acts: set[LearnedLiftedAction] = set()
    lift_flu: set[LearnedLiftedFluent] = set()

    # LOAD TRUCK ACT
    load_truck_pre = {LearnedLiftedFluent("at", ["obj", "location"], [0, 2])}
    load_truck_pre.add(LearnedLiftedFluent("at", ["truck", "location"], [1, 2]))
    load_truck_pre.add(LearnedLiftedFluent("package", ["package"], [0]))
    load_truck_pre.add(LearnedLiftedFluent("truck", ["truck"], [1]))
    load_truck_pre.add(LearnedLiftedFluent("location", ["location"], [2]))
    load_truck_eff_add = {LearnedLiftedFluent("in", ["package", "truck"], [0, 1])}
    load_truck_eff_delete = {LearnedLiftedFluent("at", ["package", "location"], [0, 2])}
    load_truck: LearnedLiftedAction = LearnedLiftedAction("load-truck",
                                                          ["package", "truck", "location"],
                                                          precond=load_truck_pre,
                                                          add=load_truck_eff_add, delete=load_truck_eff_delete)
    lift_acts.add(load_truck)
    lift_flu.update(load_truck_pre, load_truck_eff_add, load_truck_eff_delete)

    # LOAD AIRPLANE ACT
    load_airplane_pre = {LearnedLiftedFluent("at", ["package", "location"], [0, 2])}
    load_airplane_pre.add(LearnedLiftedFluent("at", ["airplane", "location"], [1, 2]))
    load_airplane_pre.add(LearnedLiftedFluent("package", ["package"], [0]))
    load_airplane_pre.add(LearnedLiftedFluent("airplane", ["airplane"], [1]))
    load_airplane_pre.add(LearnedLiftedFluent("location", ["location"], [2]))
    load_airplane_eff_add = {LearnedLiftedFluent("in", ["package", "airplane"], [0, 1])}
    load_airplane_eff_delete = {LearnedLiftedFluent("at", ["package", "location"], [0, 2])}
    load_airplane: LearnedLiftedAction = LearnedLiftedAction("load-airplane",
                                                             ["package", "truck", "location"],
                                                             precond=load_airplane_pre,
                                                             add=load_airplane_eff_add,
                                                             delete=load_airplane_eff_delete)
    lift_acts.add(load_airplane)
    lift_flu.update(load_airplane_eff_delete, load_airplane_eff_add, load_airplane_pre)

    unload_truck_pre = {LearnedLiftedFluent("at", ["truck", "location"], [1, 2])}
    unload_truck_pre.add(LearnedLiftedFluent("in", ["package", "truck"], [0, 1]))
    unload_truck_pre.add(LearnedLiftedFluent("package", ["package"], [0]))
    unload_truck_pre.add(LearnedLiftedFluent("truck", ["truck"], [1]))
    unload_truck_pre.add(LearnedLiftedFluent("location", ["location"], [2]))
    unload_truck_eff_add = {LearnedLiftedFluent("at", ["package", "location"], [0, 2])}
    unload_truck_eff_delete = {LearnedLiftedFluent("in", ["package", "truck"], [0, 1])}
    unload_truck: LearnedLiftedAction = LearnedLiftedAction("unload-truck",
                                                            ["package", "truck", "location"],
                                                            precond=unload_truck_pre,
                                                            add=unload_truck_eff_add,
                                                            delete=unload_truck_eff_delete)
    lift_acts.add(unload_truck)
    lift_flu.update(unload_truck_pre, unload_truck_eff_add, unload_truck_eff_delete)

    unload_airplane_pre = {LearnedLiftedFluent("at", ["airplane", "location"], [1, 2])}
    unload_airplane_pre.add(LearnedLiftedFluent("in", ["package", "airplane"], [0, 1]))
    unload_airplane_pre.add(LearnedLiftedFluent("package", ["package"], [0]))
    unload_airplane_pre.add(LearnedLiftedFluent("airplane", ["airplane"], [1]))
    unload_airplane_pre.add(LearnedLiftedFluent("location", ["location"], [2]))
    unload_airplane_eff_add = {LearnedLiftedFluent("at", ["package", "location"], [0, 2])}
    unload_airplane_eff_delete = {LearnedLiftedFluent("in", ["package", "airplane"], [0, 1])}
    unload_airplane: LearnedLiftedAction = LearnedLiftedAction("unload_airplane",
                                                               ["package", "airplane", "location"],
                                                               precond=unload_airplane_pre,
                                                               add=unload_airplane_eff_add,
                                                               delete=unload_airplane_eff_delete)
    lift_acts.add(unload_airplane)
    lift_flu.update(unload_airplane_pre, unload_airplane_eff_add, unload_airplane_eff_delete)

    # "drive-truck": ["truck", "location", "location", "city"],
    # "fly-airplane": ["airplane", "location", "location"]}
    drive_truck_pre = {LearnedLiftedFluent("at", ["truck", "location"], [0, 1])}
    drive_truck_pre.add(LearnedLiftedFluent("truck", ["truck"], [0]))
    drive_truck_pre.add(LearnedLiftedFluent("location", ["location"], [1]))
    drive_truck_pre.add(LearnedLiftedFluent("location", ["location"], [2]))
    drive_truck_pre.add(LearnedLiftedFluent("city", ["city"], [3]))
    drive_truck_pre.add(LearnedLiftedFluent("in-city", ["location", "city"], [1, 3]))
    drive_truck_pre.add(LearnedLiftedFluent("in-city", ["location", "city"], [2, 3]))

    drive_truck_eff_add = {LearnedLiftedFluent("at", ["truck", "location"], [0, 2])}
    drive_truck_eff_delete = {LearnedLiftedFluent("at", ["truck", "location"], [0, 2])}
    drive_truck: LearnedLiftedAction = LearnedLiftedAction("drive-truck",
                                                           ["truck", "location", "location", "city"],
                                                           precond=drive_truck_pre,
                                                           add=drive_truck_eff_add,
                                                           delete=drive_truck_eff_delete)
    lift_acts.add(drive_truck)
    lift_flu.update(drive_truck_eff_add, drive_truck_eff_delete, drive_truck_pre)

    fly_airplane_pre = {LearnedLiftedFluent("at", ["airplane", "location"], [0, 1])}
    fly_airplane_pre.add(LearnedLiftedFluent("airplane", ["airplane"], [0]))
    fly_airplane_pre.add(LearnedLiftedFluent("airport", ["airport"], [1]))
    fly_airplane_pre.add(LearnedLiftedFluent("airport", ["airport"], [2]))
    fly_airplane_eff_add = {LearnedLiftedFluent("at", ["airplane", "location"], [0, 2])}
    fly_airplane_eff_delete = {LearnedLiftedFluent("at", ["airplane", "location"], [0, 2])}
    fly_airplane: LearnedLiftedAction = LearnedLiftedAction("fly_airplane",
                                                            ["airplane", "location", "location"],
                                                            precond=drive_truck_pre,
                                                            add=drive_truck_eff_add,
                                                            delete=drive_truck_eff_delete)
    lift_acts.add(fly_airplane)
    lift_flu.update(fly_airplane_eff_add, fly_airplane_eff_delete, fly_airplane_pre)

    return Model(lift_flu, lift_acts)

def make_locm_pre_dict() -> dict[str,list[str]]:
    return {"load-truck": ['(package, 0)', '(truck, 1)', '(location, 2)'],
                         "unload-truck": ['(package, 0)', '(truck, 1)', '(location, 2)'],
                         "load-airplane": ['(package, 0)', '(airplane, 1)', '(location, 2)'],
                         "unload-airplane": ['(package, 0)', '(airplane, 1)', '(location, 2)'],
                         "drive-truck": ['(truck, 1)', '(location, 1)', '(location, 2)', '(city, 3)'],
                         "fly-airplane": ['(airplane, 1)', '(airport, 1)', '(airport, 2)']}

class TestSAMgenerator(TestCase):
    # all logistic domain info for tests
    log_model: Model
    action_2_sort_log = {"load-truck": ["obj", "obj", "loc"],
                         "unload-truck": ["obj", "obj", "loc"],
                         "load-airplane": ["obj", "obj", "loc"],
                         "unload-airplane": ["obj", "obj", "loc"],
                         "drive-truck": ["obj", "loc", "loc", "cit"],
                         "fly-airplane": ["obj", "loc", "loc"]}

    def setUp(self) -> None:
        self.log_model = make_log_model()
        # setting up the logistic hand made action model

    def test_model_extraction_1_logistics(self):
        generator: TraceFromGoal = TraceFromGoal(problem_id=1481, observe_pres_effs=True)
        base = Path(__file__).parent.parent
        model_dom = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_domain.pddl").resolve()
        )
        model_prob = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_prob.pddl").resolve()
        )
        generator.change_goal({
            get_fluent(
                "at",
                ["package package6", "location city1-2"]
            ),
            get_fluent(
                "at",
                ["package package5", "location city6-2"]
            ),
            get_fluent(
                "at",
                ["package package4", "location city3-2"]
            ),
            get_fluent(
                "at",
                ["package package3", "location city6-1"]
            ),
            get_fluent(
                "at",
                ["package package2", "location city6-2"]
            ),
            get_fluent(
                "at",
                ["package package1", "location city2-1"]
            )
        }, model_dom, model_prob)
        traces = [generator.generate_trace()]
        # prob 2
        generator = TraceFromGoal(problem_id=1496)
        generator.change_goal({
            get_fluent(
                "at",
                ["package obj31", "location apt4"]
            ),
            get_fluent(
                "at",
                ["package obj22", "location apt2"]
            ),
            get_fluent(
                "at",
                ["package obj42", "location apt4"]
            ),
            get_fluent(
                "at",
                ["package obj53", "location apt3"]
            ),
            get_fluent(
                "at",
                ["package obj12", "location pos1"]
            ),
            get_fluent(
                "at",
                ["package obj32", "location apt1"]
            ),
            get_fluent(
                "at",
                ["package obj43", "location apt3"]
            ),
            get_fluent(
                "at",
                ["package obj52", "location apt1"]
            ),
            get_fluent(
                "at",
                ["package obj51", "location apt3"]
            ),
            get_fluent(
                "at",
                ["package obj21", "location apt4"]
            ),
            get_fluent(
                "at",
                ["package obj11", "location pos3"]
            ),
            get_fluent(
                "at",
                ["package obj23", "location pos4"]
            ),
            get_fluent(
                "at",
                ["package obj33", "location pos3"]
            ),
            get_fluent(
                "at",
                ["package obj13", "location apt3"]
            ),
            get_fluent(
                "at",
                ["package obj41", "location pos1"]
            )
        }, model_dom, model_prob)
        traces.append(generator.generate_trace())
        trace_list: TraceList = TraceList(traces=traces)
        sam_generator: sam.SAMgenerator = sam.SAMgenerator(trace_list=trace_list, action_2_sort=self.action_2_sort_log)
        sam_model: Model = sam_generator.generate_model()

        print(sam_model.details())
        print("\n\n\n\n===================================")
        model_dom = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_domain_copy.pddl").resolve()
        )
        model_prob = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_prob_copy.pddl").resolve()
        )
        sam_model.to_pddl('logistics', 'log00_x',model_dom, model_prob)


        # using locm for comparison
        # lc_model: Model = LOCM(ObservedTraceList(trace_list,ActionObservation), make_locm_pre_dict())
        # lc_model.to_pddl('logistics', 'log00_x', 'new_domain_copy.pddl', 'new_prob_copy.pddl')



    def test_model_extraction_2_logistics(self):
        base = Path(__file__).parent.parent
        model_dom = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_domain.pddl").resolve()
        )
        model_prob = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_prob.pddl").resolve()
        )
        generator: TraceFromGoal = TraceFromGoal(problem_id=1481, observe_pres_effs=True)
        generator.change_goal({
            get_fluent(
                "at",
                ["package package6", "location city1-2"]
            ),
            get_fluent(
                "at",
                ["package package5", "location city6-2"]
            )
        }, model_dom, model_prob)
        traces: list[Trace] = [generator.generate_trace()]
        # prob 2
        generator = TraceFromGoal(problem_id=1496)

        generator.change_goal({
            get_fluent(
                "at",
                ["package obj31", "location apt4"]
            ),
            get_fluent(
                "at",
                ["package obj22", "location apt2"]
            ),
            get_fluent(
                "at",
                ["package obj42", "location apt4"]
            ),
            get_fluent(
                "at",
                ["package obj53", "location apt3"]
            ),
            get_fluent(
                "at",
                ["package obj12", "location pos1"]
            ),
            get_fluent(
                "at",
                ["package obj32", "location apt1"]
            )
        },model_dom, model_prob)
        traces.append(generator.generate_trace())
        trace_list: TraceList = TraceList(traces=traces)
        sam_generator: sam.SAMgenerator = sam.SAMgenerator(trace_list=trace_list, action_2_sort=self.action_2_sort_log)
        sam_model: Model = sam_generator.generate_model()
        print(f"MODEL 2 \n{sam_model.details()}")
        print("\n\n\n\n===================================")
        model_dom = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_domain_copy_2.pddl").resolve()
        )
        model_prob = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_prob_copy_2.pddl").resolve()
        )
        sam_model.to_pddl('logistics', 'log00_x', model_dom, model_prob)

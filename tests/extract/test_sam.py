from pathlib import Path
from unittest import TestCase
from macq.trace import Fluent, PlanningObject, TraceList, Trace
from macq.generate.pddl import TraceFromGoal
from macq.extract import Model, sam


# !!!note to self: need to change goal fluents to the original goal(even if it set automatically)
# because an error accuses

def get_fluent(name: str, objs: list[str]):
    objects = [PlanningObject(o.split()[0], o.split()[1])
               for o in objs]
    return Fluent(name, objects)


# def fix_states_4TraceList(trace_list: TraceList): # TODO test this!!!!
#     for trace in trace_list.traces:
#         pre_cond_set: set[Fluent] = set({})
#         action_pred_to_add: set[Fluent] = set({})
#         for step in trace.steps:
#             if step.action:
#                 action_pred_to_add.update(f for f in step.action.precond)
#                 step.state.fluents.update({p, True} for p in action_pred_to_add)
#                 action_pred_to_add.difference({p for p in step.action.delete})
#                 try:
#                     if trace.steps.__getitem__(step.index + 1):
#                         trace.steps.__getitem__(step.index+1).state.fluents.update(
#                             {p, True} for p in action_pred_to_add)
#                 finally:
#                     continue
#
#         to_add: set[Fluent] = pre_cond_set.difference(trace.fluents)
#         for step in trace:
#             step.state.fluents.update({pre, True} for pre in to_add)


class TestSAMgenerator(TestCase):
    # all logistic domain info for tests
    log_model: Model
    action_2_sort_log = {"load-truck": ["obj", "obj", "loc"],
                         "unload-truck": ["obj", "obj", "loc"],
                         "load-airplane": ["obj", "obj", "loc"],
                         "unload-airplane": ["obj", "obj", "loc"],
                         "drive-truck": ["obj", "loc", "loc", "cit"],
                         "fly-airplane": ["obj", "loc", "loc"]}

    def setUp(self) -> None: pass
    # setting up the logistic hand made action model

    def test_model_extraction_1_logistics(self):
        generator: TraceFromGoal = TraceFromGoal(problem_id=1481, observe_pres_effs=True, observe_static_fluents=True)
        generator.observe_static_fluents = True
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
        generator = TraceFromGoal(problem_id=1496, observe_pres_effs=True, observe_static_fluents=True)
        generator.observe_static_fluents = True
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
        from macq.observation import IdentityObservation
        sam_generator: sam.SAMgenerator = sam.SAMgenerator(obs_trace_list=trace_list.tokenize(
            Token=IdentityObservation), action_2_sort=self.action_2_sort_log)
        sam_model: Model = sam_generator.generate_model()

        print(sam_model.details())
        print("\n\n\n\n===================================")
        model_dom = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_domain_copy.pddl").resolve()
        )
        model_prob = str(
            (base / "pddl_testing_files/sam_pddl_runtime_generated_pddls/new_prob_copy.pddl").resolve()
        )
        sam_model.to_pddl('logistics', 'log00_x', model_dom, model_prob)

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
        generator: TraceFromGoal = TraceFromGoal(problem_id=1481, observe_pres_effs=True, observe_static_fluents=True)
        generator.generate_trace()
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
        generator = TraceFromGoal(problem_id=1496, observe_pres_effs=True, observe_static_fluents=True)
        generator.observe_static_fluents = True
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
        }, model_dom, model_prob)
        traces.append(generator.generate_trace())
        trace_list: TraceList = TraceList(traces=traces)
        import macq
        sam_generator: sam.SAMgenerator = sam.SAMgenerator(obs_trace_list=trace_list.tokenize(
            Token=macq.observation.identity_observation.IdentityObservation), action_2_sort=self.action_2_sort_log)
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

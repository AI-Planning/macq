from macq import generate
from macq.trace import Fluent, PlanningObject, TraceList

goal_generator = generate.pddl.TraceFromGoal(problem_id=4398)
# goal_generator.change

goal_generator.change_init(
    {
        Fluent("on", [PlanningObject("object", "f"), PlanningObject("object", "a")]),
        Fluent("on", [PlanningObject("object", "e"), PlanningObject("object", "f")]),
        Fluent("clear", [PlanningObject("object", "e")]),
        Fluent("clear", [PlanningObject("object", "c")]),
        Fluent("ontable", [PlanningObject("object", "c")]),
        Fluent("ontable", [PlanningObject("object", "a")]),
        Fluent("handempty", [])
    }
)
goal_generator.change_goal({
    Fluent("on", [PlanningObject("object", "a"), PlanningObject("object", "c")]),
    Fluent("on", [PlanningObject("object", "e"), PlanningObject("object", "a")])
})
goal_generator.generate_trace()
TraceList([goal_generator.trace]).print()
print()
# traces = generate.pddl.VanillaSampling(problem_id=4398, plan_len=25).traces
# traces.print()
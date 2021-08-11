from macq.trace import *
from macq.extract import Extract, modes
from macq.observation import PartialObservation
from macq.generate.pddl import *


def get_fluent(name: str, objs: list[str]):
    objects = [PlanningObject(o.split()[0], o.split()[1]) for o in objs]
    return Fluent(name, objects)


if __name__ == "__main__":
    traces = TraceList()
    generator = TraceFromGoal(problem_id=1801)
    # for f in generator.trace.fluents:
    #     print(f)

    generator.change_goal(
        {
            get_fluent("communicated_soil_data", ["waypoint waypoint2"]),
            get_fluent("communicated_rock_data", ["waypoint waypoint3"]),
            get_fluent(
                "communicated_image_data", ["objective objective1", "mode high_res"]
            ),
        }
    )
    traces.append(generator.generate_trace())
    generator.change_goal(
        {
            get_fluent("communicated_soil_data", ["waypoint waypoint0"]),
            get_fluent("communicated_rock_data", ["waypoint waypoint1"]),
            get_fluent(
                "communicated_image_data", ["objective objective1", "mode high_res"]
            ),
        }
    )
    traces.append(generator.generate_trace())
    # traces.print("color")

    observations = traces.tokenize(PartialObservation, percent_missing=0.5)
    # model = Extract(observations, modes.ARMS, upper_bound=2, debug=True)
    model = Extract(
        observations,
        modes.ARMS,
        debug=False,
        upper_bound=5,
        min_support=2,
        action_weight=110,
        info_weight=100,
        threshold=0.66,
        info3_default=30,
        plan_default=30,
    )
    print(model.details())

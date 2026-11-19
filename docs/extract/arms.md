### ARMS

#### Usage

```python
from macq import generate, extract
from macq.core import GroundedFluent, ObjectType, PlanningObject
from macq.trace import TraceList
from macq.observation import PartialObservation

def get_fluent(name: str, objs: list[str]):
    objects = [PlanningObject(o.split()[1], ObjectType(o.split()[0])) for o in objs]
    return GroundedFluent(name, objects)

traces = TraceList()
generator = generate.pddl.TraceFromGoal(problem_id=1801)

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
        get_fluent("communicated_soil_data", ["waypoint waypoint2"]),
        get_fluent("communicated_rock_data", ["waypoint waypoint3"]),
        get_fluent(
            "communicated_image_data", ["objective objective1", "mode high_res"]
        ),
    }
)
traces.append(generator.generate_trace())

observations = traces.tokenize(PartialObservation, percent_missing=0.60)
model = extract.Extract(
    observations,
    extract.modes.ARMS,
    upper_bound=2,
    min_support=2,
    action_weight=110,
    info_weight=100,
    threshold=0.6,
    info3_default=30,
    plan_default=30,
)

print(model.details())
```

**Output:**

```text
Domain model:
  Fluents: (at x0 rover x1 waypoint), (at_rock_sample x0 waypoint), (channel_free x0 lander), (have_rock_analysis x0 rover x1 waypoint), ...
  Actions:
    (communicate_image_data x0 rover x1 waypoint x2 mode x3 objective x4 lander x5 waypoint):
      precond:
        (at_rock_sample 5)
        (at_soil_sample 1)
        (channel_free 4)
        (communicated_rock_data 1)
        (have_rock_analysis 0 1)
      add:
        (at 0 1)
        (communicated_image_data 3 2)
        (have_image 0 3 2)
      delete:
        (channel_free 4)
    ...
```

ARMS returns a lifted domain model. Each fluent inside an action lists the indices of the action parameters that fill its arguments, chosen from the bindings seen most often in the observations.

ARMS can learn a relation that an action's parameters can't fill, such as a relation over a `camera` on an action with no `camera` parameter. These relations can't be stated in a lifted domain model, so ARMS drops each one and issues a warning.

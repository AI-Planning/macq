### ARMS

#### Usage

```python
from macq import generate, extract
from macq.trace import PlanningObject, Fluent, TraceList
from macq.observation import PartialObservation

def get_fluent(name: str, objs: list[str]):
    objects = [PlanningObject(o.split()[0], o.split()[1]) for o in objs]
    return Fluent(name, objects)

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
Model:
  Fluents: (at rover rover0 waypoint waypoint2), (have_soil_analysis rover rover0 waypoint waypoint2), (have_soil_analysis rover rover0 waypoint waypoint3), ...
  Actions:
    (communicate_image_data rover waypoint mode objective lander waypoint):
      precond:
        calibrated camera rover
        have_rock_analysis rover waypoint
        communicated_rock_data waypoint
        channel_free lander
        at_soil_sample waypoint
        at_rock_sample waypoint
      add:
        calibrated camera rover
        at rover waypoint
        have_image rover objective mode
        channel_free lander
        communicated_image_data objective mode
      delete:
        calibrated camera rover
    ...
```

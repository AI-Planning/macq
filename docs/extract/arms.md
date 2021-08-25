# Usage

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
model.details()
```

**Output:**
```text
```

# API Documentation

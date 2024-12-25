### Observer

#### Usage

```python
from macq import generate, extract
from macq.observation import IdentityObservation

traces = generate.pddl.VanillaSampling(problem_id=123, plan_len=20, num_traces=100).traces
observations = traces.tokenize(IdentityObservation)
model = extract.Extract(observations, extract.modes.OBSERVER)

print(model.details())
```

**Output:**

```text
Model:
  Fluents: at stone stone-03 location pos-04-06, at stone stone-01 location pos-04-06, at stone stone-02 location pos-05-06, at stone stone-06 location pos-07-04, at stone stone-11 ...
  Actions:
    push-to-goal stone stone-04 location pos-04-05 location pos-04-06 direction dir-up location pos-04-04 player player-01:
      precond:
        at player player-01 location pos-04-06
        at stone stone-04 location pos-04-05
        clear location pos-05-06
        ...
      add:
        at stone stone-04 location pos-04-04
        clear location pos-04-06
        at-goal stone stone-04
        at player player-01 location pos-04-05
      delete:
        at stone stone-04 location pos-04-05
        clear location pos-04-04
        at player player-01 location pos-04-06
  ...
```

# SLAF

## Usage

```python
from macq import generate, extract
from macq.observation import AtomicPartialObservation

traces = generate.pddl.VanillaSampling(problem_id=4398, plan_len=2, num_traces=1).traces
observations = traces.tokenize(AtomicPartialObservation, percent_missing=0.10)
model = Extract(observations, extract.modes.SLAF)
print(model.details())
```

**Output:**

```text
Model:
  Fluents: clear location pos-06-09, clear location pos-02-05, clear location pos-08-08, clear location pos-10-05, ...
  Actions:
    move player player-01 direction dir-left location pos-05-02 location pos-06-02:
      precond:
      add:
      delete:
        (clear location pos-05-02)
        (at player player-01 location pos-06-02)
        ...
    ...
```

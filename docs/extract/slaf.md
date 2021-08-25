# Usage

```python
from macq import generate, extract
from macq.observation import AtomicPartialObservation

traces = generate.pddl.VanillaSampling(problem_id=123, plan_len=2, num_traces=1).traces
observations = traces.tokenize(AtomicPartialObservation, percent_missing=0.10)
model = Extract(observations, extract.modes.SLAF)
print(model.details())
```

**Output:**
```text
Model:
  Fluents: clear location pos-06-09, clear location pos-02-05, clear location pos-08-08, clear location pos-10-05, clear location pos-02-06, clear location pos-10-02, clear location pos-01-01, at stone stone-05 location pos-08-05, at stone stone-07 location pos-08-06, at stone stone-03 location pos-07-04, clear location pos-03-06, clear location pos-10-06, clear location pos-10-10, clear location pos-05-09, clear location pos-05-07, clear location pos-02-07, clear location pos-09-01, at stone stone-06 location pos-04-06, clear location pos-02-03, clear location pos-07-05, clear location pos-09-10, clear location pos-06-05, at stone stone-01 location pos-05-04, clear location pos-02-10, clear location pos-06-10, clear location pos-11-03, at stone stone-11 location pos-06-08, at stone stone-08 location pos-04-07, clear location pos-01-10, clear location pos-07-03, clear location pos-02-11, clear location pos-03-01, clear location pos-06-02, clear location pos-03-02, clear location pos-11-01, clear location pos-06-03, clear location pos-08-04, clear location pos-09-11, at stone stone-09 location pos-08-07, clear location pos-09-07, clear location pos-06-07, clear location pos-10-01, clear location pos-11-09, clear location pos-03-05, clear location pos-07-06, clear location pos-05-05, at stone stone-12 location pos-07-08, clear location pos-10-03, clear location pos-11-11, clear location pos-10-09, clear location pos-02-01, clear location pos-02-02, clear location pos-01-02, at stone stone-02 location pos-06-04, clear location pos-03-10, clear location pos-05-10, clear location pos-07-10, clear location pos-09-05, clear location pos-07-09, clear location pos-05-03, clear location pos-10-11, clear location pos-01-03, at stone stone-04 location pos-04-05, clear location pos-07-02, clear location pos-09-06, clear location pos-10-07, clear location pos-01-09, clear location pos-03-07, clear location pos-04-04, clear location pos-01-11
  Actions:
    move player player-01 direction dir-left location pos-05-02 location pos-06-02:
      precond:
      add:
      delete:
        (clear location pos-05-02)
        (at player player-01 location pos-06-02)
```

# API Documentation

# MAcq: The Model Acquisition Toolkit

[![CI](https://github.com/ai-planning/macq/actions/workflows/CI.yml/badge.svg)](https://github.com/ai-planning/macq/actions)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/haz/03ac305b42d7c9ad4ef3213341bf3f2f/raw/macq__heads_main.json?cacheSeconds=3600)](https://github.com/ai-planning/macq/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-MIT-purple)](https://github.com/ai-planning/macq/blob/main/LICENSE)

This library is a collection of tools for planning-like action model acquisition from state trace data. It contains a reimplementation from many existing works, and generalizes some of them to new settings.

## Usage

```python
from macq import generate, extract
from macq.observation import IdentityObservation, AtomicPartialObservation

# get a domain-specific generator: uses api.planning.domains problem_id/
# generate 100 traces of length 20 using vanilla sampling
traces = generate.pddl.VanillaSampling(problem_id = 123, plan_len = 20, num_traces = 100).traces

traces.generate_more(10)

action1 = traces[0][0].action
traces.get_usage(action1)
[0.05, 0.05, ..., 0.05]

trace = traces[0]
len(trace)
20

trace.fluents
trace.actions
trace.get_pre_states(action) # get the state before each occurance of action
trace.get_post_states(action) # state after each occurance of action
trace.get_total_cost()
```

## Survey

You can find the full scope of papers considered in the survey (implemented and otherwise) at http://macq.planning.domains . This repository of model acquisition techniques will be added to over time.

## Survey Papers

* [A Review of Machine Learning for Automated Planning](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.231.4901&rep=rep1&type=pdf) (see Fig 2)
* [A Review of Learning Planning Action Models](https://hal.archives-ouvertes.fr/hal-02010536/document) (see Tbl 3)

## Citing this work

```latex
@inproceedings{macq-keps-2022,
  author    = {Ethan Callanan and Rebecca De Venezia and Victoria Armstrong and Alison Paredes and Tathagata Chakraborti and Christian Muise},
  title     = {MACQ: A Holistic View of Model Acquisition Techniques},
  booktitle = {The ICAPS Workshop on Knowledge Engineering for Planning and Scheduling (KEPS)},
  year      = {2022}
}
```

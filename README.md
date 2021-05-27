# MAcq: The Model Acquisition Toolkit

This library is a collection of tools for planning-like action model acquisition from state trace data. It contains a reimplementation from many existing works, and generalizes some of them to new settings.

Install for development by cloning the repository and running `pip install .[dev]` (use `pip3` if you have python2 installed).

## Usage
```python
from macq import generate, extract
from macq.observation import IdentityObservation

# domain-specific generator: uses api.planning.domains problem_id
blocks_gen = generate.pddl.Generator(problem_id = 123)

# further configuration
blocks_gen.configure(
  {
    'length': 20, # 20 steps long
    'use_goal': True,
    'diversity': True,
    'method': generate.pddl.modes.MC
  }
)

# generate 100 traces
traces = generate.Generate(generator=blocks_gen, traces=100)

more_traces = traces.generate_more(10)

traces.get_usage(action)

trace = traces[0]
trace.fluents
trace.actions
trace.get_prev_states(action) # get the state before each occurance of action
trace.get_post_states(action) # state after each occurance of action
trace.get_total_cost()
trace.tokenize(IdentityObservation)
trace.tokens

step = trace[0]
step.base_fluents()
step.base_action()

model = extract.Extract(traces, extract.modes.OBSERVER)

model.actions
...

model.actions[0].to_pddl()

```

## Coverage

- [ ] [Rule Creation and Rule Learning through Environmental Exploration](https://www.ijcai.org/Proceedings/89-1/Papers/108.pdf) (IJCAI'89)
- [ ] [Learning by Experimentation: The Operator Refinement Method](https://kilthub.cmu.edu/articles/journal_contribution/Learning_by_Experimentation_The_Operator_Refinement_Method/6622868/1) (MLBook'90)
- [ ] [Learning Planning Operators by Observation and Practice](https://aaai.org/Papers/AIPS/1994/AIPS94-057.pdf) (AIPS'94)
- [ ] [Learning by Experimentation: Incremental Refinement of Incomplete Planning Domains](https://www.sciencedirect.com/science/article/pii/B9781558603356500192) (ICML'94)
- [ ] [Learning Probabilistic Relational Planning Rules](https://people.csail.mit.edu/lpk/papers/2005/zpk-aaai05.pdf) (ICAPS'04)
- [ ] [Learning Action Models from Plan Examples with Incomplete Knowledge](https://www.aaai.org/Papers/ICAPS/2005/ICAPS05-025.pdf) (ICAPS'05)
- [ ] [Learning Planning Rules in Noisy Stochastic Worlds](https://people.csail.mit.edu/lpk/papers/2005/zpk-aaai05.pdf) (AAAI'05)
- [ ] [Learning action models from plan examples using weighted MAX-SAT](https://www.sciencedirect.com/science/article/pii/S0004370206001408) (AIJ'07)
- [ ] [Learning Symbolic Models of Stochastic Domains](https://www.aaai.org/Papers/JAIR/Vol29/JAIR-2910.pdf) (JAIR'07)
- [ ] [Learning Partially Observable Deterministic Action Models](https://www.aaai.org/Papers/JAIR/Vol33/JAIR-3310.pdf) (JAIR'08)
- [ ] [Acquisition of Object-Centred Domain Models from Planning Examples](https://ojs.aaai.org/index.php/ICAPS/article/view/13391) (ICAPS'09)
- [ ] [Automated acquisition of action knowledge](http://eprints.hud.ac.uk/id/eprint/3292/1/mccluskeyCRC.pdf) (ICAART'09)
- [ ] [Generalised Domain Model Acquisition from Action Traces](https://ojs.aaai.org/index.php/ICAPS/article/view/13476) (ICAPS'11)
- [ ] [Autonomous Learning of Action Models for Planning](https://papers.nips.cc/paper/2011/file/4671aeaf49c792689533b00664a5c3ef-Paper.pdf) (NeurIPS'11)
- [ ] [Learning STRIPS Operators from Noisy and Incomplete Observations](https://arxiv.org/abs/1210.4889) (UAI'12)
- [ ] [Action-Model Acquisition from Noisy Plan Traces](http://rakaposhi.eas.asu.edu/camera-noise.pdf) (IJCAI'13)
- [ ] [Action-model acquisition for planning via transfer learning](https://www.sciencedirect.com/science/article/pii/S0004370214000320) (AIJ'14)
- [ ] [Discovering Underlying Plans Based on Distributed Representations of Actions](http://rakaposhi.eas.asu.edu/aamas16-hankz.pdf) (AAMAS'16)
- [ ] [Domain Model Acquisition in Domains with Action Costs](https://ojs.aaai.org/index.php/ICAPS/article/view/13762) (ICAPS'16)
- [ ] [Domain Model Acquisition in the Presence of Static Relations in the LOP System](https://www.ijcai.org/Proceedings/16/Papers/622.pdf) (IJCAI'16)
- [ ] [Efficient, Safe, and Probably Approximately Complete Learning of Action Models](https://arxiv.org/abs/1705.08961) (IJCAI'17)
- [ ] [Robust planning with incomplete domain models](https://www.sciencedirect.com/science/article/pii/S0004370216301539) (AIJ'17)
- [ ] [LOUGA: Learning Planning Operators Using Genetic Algorithms](https://www.springerprofessional.de/en/louga-learning-planning-operators-using-genetic-algorithms/15981308) (PRKAW'18)
- [ ] [Learning STRIPS Action Models with Classical Planning](https://arxiv.org/abs/1903.01153) (ICAPS'18)
- [ ] [Learning Planning Operators from Episodic Traces](https://aaai.org/ocs/index.php/SSS/SSS18/paper/view/17594/15530) (AAAI-SS'18)
- [ ] [Learning action models with minimal observability](https://www.sciencedirect.com/science/article/abs/pii/S0004370218304259) (AIJ'19)
- [ ] [Learning Action Models from Disordered and Noisy Plan Traces](https://arxiv.org/abs/1908.09800) (arXiv'19)
- [ ] [Bridging the Gap: Providing Post-Hoc Symbolic Explanations for Sequential Decision-Making Problems with Black Box Simulators](https://arxiv.org/abs/2002.01080) (ICML-WS'20)
- [ ] [STRIPS Action Discovery](https://arxiv.org/abs/2001.11457) (arXiv'20)
- [ ] [Learning First-Order Symbolic Representations for Planning from the Structure of the State Space](https://arxiv.org/abs/1909.05546) (ECAI'20)
- [ ] [Discovering Underlying Plans Based on Shallow Models](https://dl.acm.org/doi/abs/10.1145/3368270) (ACM TIST'20)
- [ ] [Agent Interrogation Algorithm](https://github.com/AAIR-lab/AIA-AAAI21) (AAAI'21)
- [ ] [Learning First-Order Representations for Planning from Black-Box States: New Results](https://arxiv.org/abs/2105.10830) (arXiv'21)

## Features / Assumptions

- Determinism:
  - Fully deterministic
  - Non-deterministic
  - Probabilistic
- Fluent observability
  - Fully observable
  - Some fluents consistently missing
  - Random fluents missing
- Parameterized
  - Atomic fluents/actions (no objects)
  - Predicates/action parameters (objects+types)
- Action observability
  - Know action names?
  - Know action parameters?
  - Know some action pre/eff?
  - Know everything?
- State noise
  - Fluents observed are correct.
  - Fluents observed may be wrong.
- Action noise
  - Obs tokens contain correct action info
  - Obs tokens may be incorrect with some probability
- Assumes rationality
  - Yes
  - Bounded
  - No

## Requirements

* Tarski

## Survey Papers

* [A Review of Machine Learning for Automated Planning](http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.231.4901&rep=rep1&type=pdf) (see Fig 2)
* [A Review of Learning Planning Action Models](https://hal.archives-ouvertes.fr/hal-02010536/document) (see Tbl 3)

## Citing this work
Coming soon...

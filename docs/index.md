# General API

## Trace Generation

These are the various methods implemented to generate the base trace data.

| Algorithm | Description |
|---|---|
| [VanillaSampling](macq/generate/pddl.html#VanillaSampling) | Samples actions uniformly at random |
| [RandomGoalSampling](macq/generate/pddl.html#RandomGoalSampling) | Samples goals by taking a random subset of a state reached after a random walk |
| [FDRandomWalkSampling](macq/generate/pddl.html#FDRandomWalkSampling) | Random walk based on a heuristic-driven depth calculation (algorithm introduced in the [FD planning system](https://www.fast-downward.org/)) |
| [TraceFromGoal](macq/generate/pddl.html#TraceFromGoal) | Generates a trace from a given domain/problem (with a goal state) |
| [CSV](macq/generate/csv.html) | Reads a CSV file to generate a trace |

## Tokenization

Once trace data is loaded, you can process the traces to produce lists of observations. The methods range from the identity observation (constaining the same data as original traces) to noisy and/or partially observable observations.

| Algorithm | Description |
|---|---|
| [IdentityObservation](macq/observation.html#IdentityObservation) | Unmodified versions of the input traces |
| [PartialObservation](macq/observation.html#PartialObservation) | Observations with a subset of the fluents hidden in the states |
| [AtomicPartialObservation](macq/observation.html#AtomicPartialObservation) | Similar to `PartialObservation`, except everything is stored as atomic strings (not fluents and parameters) |
| [ActionObservation](macq/observation.html#ActionObservation) | Observations with only the actions listed (i.e., states discarded) |
| [NoisyObservation](macq/observation.html#NoisyObservation) | Observations with added noise to the fluents |
| [NoisyPartialObservation](macq/observation.html#NoisyPartialObservation) | Observations with added noise to the fluents and a subset of the fluents hidden in the states |
| [NoisyPartialDisorderedParallelObservation](macq/observation.html#NoisyPartialDisorderedParallelObservation) | Observations with added noise to the fluents and a subset of the fluents hidden in the states, with the actions disordered and parallelized |

## Extraction Techniques

Depending on the observation type, different extraction techniques can be used to extract the relevant information from the observations. These are currently the techniques implemented:

| Algorithm | Trace Type | Paper |
|---|---|---|
| [**Observer**](macq/extract.html#observer) | [IdentityObservation](macq/observation.html#IdentityObservation) | [[1](https://aaai.org/Papers/AIPS/1994/AIPS94-057.pdf)] |
| [**SLAF**](macq/extract.html#slaf) | [AtomicPartialObservation](macq/observation.html#AtomicPartialObservation) | [[1](https://arxiv.org/abs/1401.3437)] |
| [**ARMS**](macq/extract.html#arms) | [PartialObservation](macq/observation.html#PartialObservation) | [[1](https://www.sciencedirect.com/science/article/pii/S0004370206001408), [2](https://aaai.org/papers/icaps-05-025-learning-action-models-from-plan-examples-with-incomplete-knowledge/)] |
| [**AMDN**](macq/extract.html#amdn) | [NoisyPartialDisorderedParallelObservation](macq/observation.html#NoisyPartialDisorderedParallelObservation) | [[1](https://arxiv.org/abs/1908.09800)] |
| [**LOCM**](macq/extract.html#locm) | [ActionObservation](macq/observation.html#ActionObservation) | [[1](https://ojs.aaai.org/index.php/ICAPS/article/view/13391), [2](http://eprints.hud.ac.uk/id/eprint/9052/1/LOCM_KER_author_version.pdf)] |

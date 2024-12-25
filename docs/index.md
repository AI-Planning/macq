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

- [Observer](macq/extract.html#observer)
- [SLAF](macq/extract.html#slaf)
- [ARMS](macq/extract.html#arms)
- [AMDN](macq/extract.html#amdn)
- [LOCM](macq/extract.html#locm)

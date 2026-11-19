### Trace files

A trace file holds one trace, or one trace's observation tokens, as JSON. It describes
only the trace, nothing about how traces are grouped into a dataset.

#### Usage

```python
from macq.generate.pddl import UniformWalkSampling
from macq.io import read_trace, write_trace
from macq.observation import PartialObservation

sampler = UniformWalkSampling("domain.pddl", "problem.pddl", seed=1, max_actions=20)
trace = sampler.generate_trace(0)
tokens = trace.tokenize(PartialObservation, percent_missing=0.3, rng=sampler.trace_rng(0, "partial"))
write_trace("0000.json", tokens, problem="p01")

read = read_trace("0000.json", "domain.pddl", "problem.pddl")
observations = read.tokenize(PartialObservation, percent_missing=0)  # ready for ARMS
```

`write_trace(path, source, problem=None)` takes a `Trace` or one trace's tokens. When
`problem` isn't given, a `Trace`'s `problem_id` is used. `read_trace(path, domain,
problem=None)` returns a `Trace` with `problem_id` set from the file, and
`read_traces(paths, domain, problem=None)` returns a `TraceList`. The domain and problem
can be filenames or parsed `pddl` objects.

To get the tokens an extractor needs, tokenize what you read at rate 0, for example
`PartialObservation` with `percent_missing=0` or `NoisyObservation` with
`percent_noisy=0`. Unknown values are kept exactly. `ActionObservation` works on files
with no states.

#### Format

Shown here with the states compacted; the exact layout is given below.

```json
{
  "format_version": 1,
  "problem": "p03",
  "states": [
    {"true": ["(at t1 L1)", "(road L1 L2)"]},
    {"true": ["(at t1 L2)", "(road L1 L2)"]}
  ],
  "actions": [
    "(drive t1 L1 L2)"
  ]
}
```

- `format_version` is the integer `1`.
- `problem` is an optional string id for the problem the trace came from.
- `actions` lists the trace's ground actions in order.
- `states` lists one more state than there are actions, so a trace with no actions has
  one state. It is left out entirely when the trace has no states, as with
  `ActionObservation`.
- A full state is `{"true": [...]}`. A partial state is `{"true": [...], "unknown":
  [...]}`, and `unknown` is present even when it's empty. All the states in a file have
  the same form. A trace or tokens with full states are written as full states, and
  `PartialObservation` tokens, or any state with an unknown value, as partial states.
- No other keys are allowed. Action costs and step indices aren't written.

Atoms and actions are written as canonical strings: the name, then each argument, separated
by one space inside parentheses, with no other whitespace, such as `"(at truck1 L1)"` or
`"(handempty)"`. Names keep the domain's case and are matched exactly when read.

The writer produces exactly `json.dumps(data, indent=2)` followed by a newline, in UTF-8,
with the keys in the order shown and each list of atoms sorted by code point, so the same
trace always gives the same bytes.

#### Reading a state

A state is read against the atom set: every type-consistent ground atom over the domain's
constants and, when one is given, the problem's objects. Atoms listed as true are true,
atoms listed as unknown are `None` in a `PartialState`, and every other atom in the atom
set is false. Files with no states read as steps with empty states.

The reader raises `InvalidTraceFile` for:

- an unknown `format_version`, or a missing or unknown key
- a string that isn't canonical
- an unsorted or repeated list
- an atom that is both true and unknown
- mixed state forms
- an unknown predicate, action or object
- the wrong number of arguments, or an argument of the wrong type
- a state count that isn't one more than the action count
- states, when the domain declares no predicates

#### Round trips

Reading a written trace gives back an equal `Trace`, as long as every state covered the full
atom set and no action carried preconditions or effects (which samplers record only with
`observe_pres_effs`). A trace's `problem_id` doesn't count towards equality. Atoms a state
leaves out are read back as false. For example, `VanillaSampling` leaves out static atoms by
default, so they come back false. The writer checks that all the states in a trace cover the
same atoms, but it can't check that they cover all of them.

The writer raises `ValueError` for:

- an empty trace
- states that cover different atoms
- tokens of which only some have states
- a missing action, or an action on the last step
- a value other than `True`, `False` or `None`
- a name that isn't a single PDDL symbol
- two fluents in one state that read the same

It raises `TypeError` for states keyed by strings, as in `AtomicPartialObservation`, so
write traces before tokenizing them atomically.

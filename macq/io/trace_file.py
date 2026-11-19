"""Reading and writing trace files.

The format is described in `docs/io/trace-file.md`.
"""
import json
from itertools import product
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from pddl import parse_domain, parse_problem
from pddl.core import Domain, Problem
from pddlutils.grounding import has_type

from ..trace import Action, Fluent, PartialState, PlanningObject, State, Step, Trace, TraceList
from ..observation import Observation, PartialObservation

FORMAT_VERSION = 1

PathLike = Union[str, Path]
Source = Union[Trace, Sequence[Observation]]


class InvalidTraceFile(Exception):
    """Raised when a trace file does not follow the trace file format."""

    def __init__(self, path, message):
        super().__init__(f"{path}: {message}")


# -- writing ---------------------------------------------------------------------


def write_trace(path: PathLike, source: Source, problem: Optional[str] = None):
    """Writes one trace, or one trace's observation tokens, to a trace file.

    A `Trace` or a list of tokens with full states is written with full states. A list
    of `PartialObservation` tokens, or any state holding an unknown (`None`) value, is
    written with partial states. Tokens without states, such as `ActionObservation`, are
    written with no states at all.

    Args:
        path (str | Path):
            Where to write the file.
        source (Trace | Sequence[Observation]):
            The trace, or the tokens of one trace, in order.
        problem (str):
            Optional; The problem id to record. Defaults to the trace's `problem_id`
            when `source` is a `Trace`, and is left out of the file when neither is set.

    Raises:
        ValueError:
            Raised if the source can't be written faithfully: it is empty, its states
            differ in which atoms they cover, only some of its tokens have states, an
            action is missing or the last step has one, a value isn't `True`, `False`
            or `None`, a name isn't a single PDDL symbol, or two fluents read the same.
        TypeError:
            Raised if a state is keyed by strings instead of fluents, as in
            `AtomicPartialObservation`.
    """
    Path(path).write_text(_dumps(source, problem), encoding="utf-8", newline="\n")


def _dumps(source: Source, problem: Optional[str]) -> str:
    if problem is None and isinstance(source, Trace):
        problem = source.problem_id
    if problem is not None and not isinstance(problem, str):
        raise ValueError(f"The problem id must be a string, not {problem!r}.")

    items = list(source)
    if not items:
        raise ValueError("Can't write an empty trace.")
    states = [item.state for item in items]
    actions = [item.action for item in items]

    if any(a is None for a in actions[:-1]):
        raise ValueError("Every step but the last must have an action.")
    if actions[-1] is not None:
        raise ValueError("The last step of a trace can't have an action.")

    data: Dict[str, object] = {"format_version": FORMAT_VERSION}
    if problem is not None:
        data["problem"] = problem

    stateless = [s is None for s in states]
    if any(stateless) and not all(stateless):
        raise ValueError("Either every token in a trace has a state or none does.")
    if not any(stateless):
        partial = (not isinstance(source, Trace)) and all(
            isinstance(item, PartialObservation) for item in items
        )
        partial = partial or any(v is None for s in states for v in s.values())
        data["states"] = _encode_states(states, partial)

    data["actions"] = [_action_text(a) for a in actions[:-1]]
    return json.dumps(data, indent=2) + "\n"


def _encode_states(states: List[State], partial: bool) -> List[dict]:
    atom_set = None
    encoded = []
    for state in states:
        texts: Dict[str, Optional[bool]] = {}
        for fluent, value in state.items():
            if not isinstance(fluent, Fluent):
                raise TypeError(
                    f"States must map fluents to values, not {type(fluent).__name__} "
                    "keys. Write the trace before tokenizing it atomically."
                )
            if not (value is None or isinstance(value, bool)):
                raise ValueError(f"The value of {fluent} must be True, False or None, not {value!r}.")
            text = _fluent_text(fluent)
            if text in texts:
                raise ValueError(f"Two fluents in one state both read {text}, so {text} appears twice.")
            texts[text] = value
        if atom_set is None:
            atom_set = set(texts)
        elif set(texts) != atom_set:
            raise ValueError(
                "Every state in a trace must cover the same atoms, so that missing atoms "
                "can be read back as false."
            )
        entry = {"true": sorted(t for t, v in texts.items() if v is True)}
        if partial:
            entry["unknown"] = sorted(t for t, v in texts.items() if v is None)
        encoded.append(entry)
    return encoded


def _symbol(name) -> str:
    text = str(name)
    if not text or any(c.isspace() or c in "()" for c in text):
        raise ValueError(f"The name {text!r} isn't a single PDDL symbol.")
    return text


def _canonical(name, arguments) -> str:
    return "(" + " ".join([_symbol(name), *[_symbol(a) for a in arguments]]) + ")"


def _fluent_text(fluent: Fluent) -> str:
    return _canonical(fluent.name, [o.name for o in fluent.objects])


def _action_text(action: Action) -> str:
    return _canonical(action.name, [o.name for o in action.obj_params])


# -- reading ---------------------------------------------------------------------


def read_trace(
    path: PathLike,
    domain: Union[PathLike, Domain],
    problem: Union[PathLike, Problem, None] = None,
) -> Trace:
    """Reads a trace file.

    Each state covers every type-consistent atom over the domain's constants and, when
    a problem is given, the problem's objects. Atoms the file lists as true are true,
    atoms it lists as unknown are `None` in a `PartialState`, and every other atom is
    false. A file with no states reads as steps with empty states.

    Args:
        path (str | Path):
            The trace file.
        domain (str | Path | Domain):
            The domain, or a domain shell, as a filename or a parsed domain.
        problem (str | Path | Problem):
            Optional; The problem the trace came from, whose objects join the domain's
            constants.

    Returns:
        The trace, with `problem_id` set from the file.

    Raises:
        InvalidTraceFile:
            Raised if the file doesn't follow the trace file format, or names a
            predicate, action or object the domain and problem don't have.
    """
    return _Reader(_domain(domain), _problem(problem)).read(path)


def read_traces(
    paths: Iterable[PathLike],
    domain: Union[PathLike, Domain],
    problem: Union[PathLike, Problem, None] = None,
) -> TraceList:
    """Reads several trace files against the same domain and problem.

    Args:
        paths (Iterable[str | Path]):
            The trace files, in the order wanted.
        domain (str | Path | Domain):
            The domain, or a domain shell, as a filename or a parsed domain.
        problem (str | Path | Problem):
            Optional; The problem the traces came from.

    Returns:
        The traces, in the order of `paths`.

    Raises:
        InvalidTraceFile:
            Raised if any file doesn't follow the trace file format.
    """
    reader = _Reader(_domain(domain), _problem(problem))
    return TraceList([reader.read(p) for p in paths])


def _domain(domain) -> Domain:
    return domain if isinstance(domain, Domain) else parse_domain(str(domain))


def _problem(problem) -> Optional[Problem]:
    if problem is None or isinstance(problem, Problem):
        return problem
    return parse_problem(str(problem))


class _Reader:
    """Checks and decodes trace files against one domain and problem."""

    def __init__(self, domain: Domain, problem: Optional[Problem]):
        self.domain = domain
        constants = {}
        for obj in [*domain.constants, *(problem.objects if problem else [])]:
            constants[str(obj.name)] = obj
        self.constants = constants
        self.objects = {
            name: PlanningObject(str(obj.type_tag or "object"), name)
            for name, obj in constants.items()
        }
        self.predicates = {str(p.name): p for p in domain.predicates}
        self.actions = {str(a.name): a for a in domain.actions}
        self._atoms: Optional[List[Fluent]] = None

    @property
    def atoms(self) -> List[Fluent]:
        """Every type-consistent ground atom, as fluents."""
        if self._atoms is None:
            names = sorted(self.constants)
            atoms = []
            for name in sorted(self.predicates):
                choices = [
                    [n for n in names if has_type(self.constants[n], term, self.domain)]
                    for term in self.predicates[name].terms
                ]
                for arguments in product(*choices):
                    atoms.append(Fluent(name, [self.objects[n] for n in arguments]))
            self._atoms = atoms
        return self._atoms

    def read(self, path: PathLike) -> Trace:
        self.path = path
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as e:
            self.fail(f"can't be read as JSON ({e})")
        if not isinstance(data, dict):
            self.fail("must hold a JSON object")

        unknown = set(data) - {"format_version", "problem", "states", "actions"}
        if unknown:
            self.fail(f"has unknown keys {sorted(unknown)}")
        for key in ("format_version", "actions"):
            if key not in data:
                self.fail(f"is missing the key {key!r}")
        version = data["format_version"]
        if type(version) is not int or version != FORMAT_VERSION:
            self.fail(f"has format_version {version!r}, but only {FORMAT_VERSION} is supported")
        problem_id = data.get("problem")
        if "problem" in data and not isinstance(problem_id, str):
            self.fail("must give the problem as a string")

        actions = [self.action(text) for text in self.strings(data["actions"], "actions")]
        if "states" in data:
            states = self.states(data["states"])
            if len(states) != len(actions) + 1:
                self.fail(
                    f"has {len(states)} states and {len(actions)} actions, but a trace "
                    "has one more state than actions"
                )
        else:
            states = [State({}) for _ in range(len(actions) + 1)]

        steps = [
            Step(state, actions[i] if i < len(actions) else None, i + 1)
            for i, state in enumerate(states)
        ]
        return Trace(steps, problem_id=problem_id)

    def fail(self, message):
        raise InvalidTraceFile(self.path, message)

    def strings(self, value, where) -> List[str]:
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            self.fail(f"must give {where} as a list of strings")
        return value

    def parse(self, text: str) -> Tuple[str, List[str]]:
        parts = text[1:-1].split(" ") if text.startswith("(") and text.endswith(")") else []
        if not parts or not all(p and not any(c.isspace() or c in "()" for c in p) for p in parts):
            self.fail(f"has {text!r}, which isn't a canonical atom or action")
        return parts[0], parts[1:]

    def arguments(self, text, terms, arguments) -> List[PlanningObject]:
        if len(arguments) != len(terms):
            self.fail(f"has {text}, but it takes {len(terms)} arguments")
        for term, name in zip(terms, arguments):
            if name not in self.constants:
                self.fail(f"has {text}, but {name} isn't an object of the domain or problem")
            if not has_type(self.constants[name], term, self.domain):
                self.fail(
                    f"has {text}, but {name} of type {self.objects[name].obj_type} "
                    f"can't fill a parameter of type {sorted(term.type_tags)}"
                )
        return [self.objects[name] for name in arguments]

    def action(self, text: str) -> Action:
        name, arguments = self.parse(text)
        if name not in self.actions:
            self.fail(f"has {text}, but the domain has no action {name}")
        return Action(name, self.arguments(text, self.actions[name].parameters, arguments))

    def atom(self, text: str) -> str:
        name, arguments = self.parse(text)
        if not self.predicates:
            self.fail(f"has the atom {text}, but the domain declares no predicates")
        if name not in self.predicates:
            self.fail(f"has {text}, but the domain has no predicate {name}")
        self.arguments(text, self.predicates[name].terms, arguments)
        return text

    def atom_list(self, value, where) -> List[str]:
        texts = [self.atom(t) for t in self.strings(value, where)]
        if len(set(texts)) != len(texts):
            self.fail(f"lists an atom twice in {where}")
        if texts != sorted(texts):
            self.fail(f"must list {where} in sorted order")
        return texts

    def states(self, value) -> List[State]:
        if not isinstance(value, list):
            self.fail("must give states as a list")
        forms = set()
        states = []
        for i, entry in enumerate(value):
            if not isinstance(entry, dict):
                self.fail(f"must give state {i} as an object")
            keys = set(entry)
            if keys not in ({"true"}, {"true", "unknown"}):
                self.fail(f"has state {i} with keys {sorted(keys)}, not true and optionally unknown")
            forms.add(frozenset(keys))
            true = set(self.atom_list(entry["true"], f"the true atoms of state {i}"))
            unknown = set()
            if "unknown" in entry:
                unknown = set(self.atom_list(entry["unknown"], f"the unknown atoms of state {i}"))
                both = true & unknown
                if both:
                    self.fail(f"has state {i} listing {sorted(both)[0]} as both true and unknown")
            values = {}
            for fluent in self.atoms:
                text = _fluent_text(fluent)
                values[fluent] = None if text in unknown else text in true
            states.append(PartialState(values) if "unknown" in entry else State(values))
        if len(forms) > 1:
            self.fail("mixes full and partial states")
        return states


from json import dumps
from typing import Set, Union, Optional, List

import tarski
import tarski.fstrips as fs
from tarski import FirstOrderLanguage
from tarski.io import fstrips as iofs
from tarski.model import create
from tarski.syntax import land
from tarski.syntax.formulas import CompoundFormula, Connective, top, Formula

from . import ObjectType
from .actions import GroundedAction, LiftedAction
from .fluents import LiftedFluent, GroundedFluent
from .model_type_validate import ModelType, ModelTypeValidator, ModelValidationError
from ..utils import ComplexEncoder


def _get_str_as_tarski_grounded_formula(name: str, lang: FirstOrderLanguage) -> Formula:
    """Converts a string (referencing an attribute of a LearnedAction, i.e., a specific precondition or effect))
    to a Formula.
    """
    return lang.get(name.replace(" ", "_"))()


class Model:
    """Class representation of an Action-model."""

    def __init__(
            self,
            fluents: Union[Set[LiftedFluent], Set[GroundedFluent]],
            actions: Union[Set[LiftedAction], Set[GroundedAction]],
            learned_sorts: Optional[List] = None,
            model_type: Optional[ModelType] = None,
            _skip_validation: bool = False
    ):
        """
        Internal constructor. Use factory methods for type-safe creation.

        Args:
            fluents: Set of fluents
            actions: Set of actions
            learned_sorts: Optional list of sorts
            model_type: Optional model type (will be detected if not provided)
            _skip_validation: Internal flag to skip validation (used by factory methods)
        """
        if not _skip_validation:
            # Validate consistency
            detected_type = ModelTypeValidator.validate_model_consistency(actions, fluents)
            if model_type and model_type != detected_type:
                raise ModelValidationError(
                    f"Specified model type {model_type.value} doesn't match "
                    f"detected type {detected_type.value}"
                )
            model_type = detected_type

        self.fluents = fluents
        self.actions = actions
        self.learned_sorts = learned_sorts
        self._model_type = model_type

    @property
    def model_type(self) -> ModelType:
        """Get the model type."""
        if self._model_type is None:
            self._model_type = ModelTypeValidator.validate_model_consistency(
                self.actions, self.fluents
            )
        return self._model_type

    def is_lifted_model(self) -> bool:
        """Check if this is a lifted model."""
        return self.model_type == ModelType.LIFTED

    def is_grounded_model(self) -> bool:
        """Check if this is a grounded model."""
        return self.model_type == ModelType.GROUNDED

    # Existing methods remain the same...
    def __eq__(self, other) -> bool:
        if not isinstance(other, Model):
            return False
        return (self.fluents == other.fluents and
                self.actions == other.actions and
                self.learned_sorts == other.learned_sorts)

    def details(self) -> str:
        """Return detailed string representation of the model."""
        indent = " " * 2
        string = f"Model ({self.model_type.value}):\n"
        string += f"{indent}Fluents: {', '.join(map(str, self.fluents))}\n"
        string += f"{indent}Actions:\n"
        for line in self._get_action_details().splitlines():
            string += f"{indent * 2}{line}\n"
        return string

    def _get_action_details(self) -> str:
        """Get detailed string representation of all actions."""
        # Implementation depends on your action classes having certain methods
        # This is a simplified version
        indent = " " * 2
        details = ""
        for action in self.actions:
            details += f"{action.name}:\n"
            # Add more details based on your action interface
        return details

    def serialize(self, filepath: Optional[str] = None) -> str:
        """Serialize the model to JSON."""
        serial = dumps(self._serialize(), cls=ComplexEncoder)
        if filepath is not None:
            with open(filepath, "w") as fp:
                fp.write(serial)
        return serial

    def _serialize(self) -> dict:
        """Internal serialization method."""
        return dict(
            fluents=list(self.fluents),
            actions=list(self.actions),
            learned_sorts=self.learned_sorts,
            model_type=self.model_type.value
        )

    def to_pddl(self, domain_name: str, problem_name: str = "",
                domain_filename: str = "", problem_filename: str = ""):
        """Export to PDDL format based on the model type."""

        if not problem_name:
            problem_name = domain_name + "_problem"
        if not domain_filename:
            domain_filename = domain_name + ".pddl"
        if not problem_filename:
            problem_filename = problem_name + ".pddl"

        if self.is_lifted_model():
            self.to_pddl_lifted(domain_name, problem_name, domain_filename, problem_filename)
        elif self.is_grounded_model():
            self.to_pddl_grounded(domain_name, problem_name, domain_filename, problem_filename)
        else:
            raise ModelValidationError(f"Cannot export {self.model_type.value} model to PDDL")

    def to_pddl_lifted(
        self,
        domain_name: str,
        problem_name: str,
        domain_filename: str,
        problem_filename: str,
    ):
        """Dumps a Model with typed lifted actions & fluents to PDDL files.

        Args:
            domain_name (str):
                The name of the domain to be generated.
            problem_name (str):
                The name of the problem to be generated.
            domain_filename (str):
                The name of the domain file to be generated.
            problem_filename (str):
                The name of the problem file to be generated.
        """

        lang = tarski.language(domain_name)
        problem = tarski.fstrips.create_fstrips_problem(
            domain_name=domain_name, problem_name=problem_name, language=lang
        )
        object_types = {"object"}
        if self.learned_sorts is not None:
            for s in self.learned_sorts:
                if isinstance(s, ObjectType) and s.type_name not in object_types:
                    if s.parent is None:
                        lang.sort(name=s.type_name)
                        object_types.add(s.type_name)
            for s in self.learned_sorts:
                if isinstance(s, ObjectType) and s.type_name not in object_types:
                    if s.parent is not None:
                        lang.sort(name=s.type_name, parent=s.parent)
                        object_types.add(s.type_name)


        if self.fluents:
            for f in self.fluents:
                param_types = [parm.object_type.type_name for parm in f.parameters]
                for object_type in param_types:
                    if object_type not in object_types:
                        lang.sort(object_type)
                        object_types.add(object_type)
                lang.predicate(f.name, *param_types)

        if self.actions:
            for a in self.actions:
                param_types = [parm.object_type.type_name for parm in a.params]
                vars = [lang.variable(f"x{i}", s) for i, s in enumerate(param_types)]

                positive_precond_list = [lang.get(f.name)(*[vars[i] for i, _ in enumerate(f.bounded_params)])
                                         for f in a.positive_preconditions]

                neg_precond_list = []
                try:
                    if a.negative_preconditions:
                        for f in a.negative_preconditions:
                            negated_predicate = CompoundFormula(
                                    Connective.Not,[lang.get(f.name)(
                                    *[vars[i] for i, _ in enumerate(f.bounded_params)])],)
                            neg_precond_list.append(negated_predicate)
                except AttributeError:
                    pass

                precond_list =  positive_precond_list + neg_precond_list
                if len(precond_list) == 1:
                    precond = precond_list[0]
                elif len(precond_list) == 0:
                    precond = top # always true

                else:
                    precond = CompoundFormula(Connective.And, precond_list,)

                adds = [lang.get(f.name)(*[vars[i] for i, _ in enumerate(f.bounded_params)]) for f in a.add_effects]  # type: ignore TODO validate for i, _ in enumerate(f.bounded_params)
                dels = [lang.get(f.name)(*[vars[i] for i, _ in enumerate(f.bounded_params)]) for f in a.delete_effects]  # type: ignore TODO for i, _ in enumerate(f.bounded_params)
                effects = [fs.AddEffect(e) for e in adds] + [fs.DelEffect(e) for e in dels]  # fmt: skip

                problem.action(
                    a.name,
                    parameters=vars,
                    precondition=precond,
                    effects=effects,
                )

        problem.init = tarski.model.create(lang)  # type: ignore
        problem.goal = land()  # type: ignore
        writer = iofs.FstripsWriter(problem)
        writer.write(domain_filename, problem_filename)

    def __to_tarski_formula(self,
                            attribute: Set[str],
                            lang: FirstOrderLanguage) -> Union[CompoundFormula, top]:
        """Converts a set of strings (referencing an attribute of a LearnedAction, i.e., its preconditions)
        to an Atom or CompoundFormula, in order to set up a tarski action.

        Args:
            attribute (Set[str]):
                The attribute to be converted to an Atom or CompoundFormula.
            lang (FirstOrderLanguage):
                The relevant language.

        Returns:
            The attribute of the LearnedAction, converted to an Atom or CompoundFormula.
        """
        # return top if there are no constraints
        if not attribute:
            return top
        # creates Atom
        elif len(attribute) == 1:
            grounding =  _get_str_as_tarski_grounded_formula(attribute, lang)  # type: ignore
            return CompoundFormula(Connective.And, [grounding],)

        # creates CompoundFormula
        else:
            return CompoundFormula(
                Connective.And, [self._get_str_as_tarski_formula(a, lang) for a in attribute],)  # type: ignore


    def to_pddl_grounded(
        self,
        domain_name: str,
        problem_name: str,
        domain_filename: str,
        problem_filename: str,
    ):
        """Dumps a Model to two PDDL files. The conversion only uses 0-arity predicates, and no types, objects,
        or parameters of any kind are used. Actions are represented as ground actions with no parameters.

        Args:
            domain_name (str):
                The name of the domain to be generated.
            problem_name (str):
                The name of the problem to be generated.
            domain_filename (str):
                The name of the domain file to be generated.
            problem_filename (str):
                The name of the problem file to be generated.
        """

        lang = tarski.language(domain_name)
        problem = tarski.fstrips.create_fstrips_problem(
            domain_name=domain_name, problem_name=problem_name, language=lang
        )
        if self.fluents:
            # create 0-arity predicates
            for f in self.fluents:
                # NOTE: want there to be no brackets in any fluents referenced as tarski adds these later.
                # fluents (their string conversion) must be in the following format: (on object a object b)
                test = str(f)
                lang.predicate(str(f)[1:-1].replace(" ", "_"))

        if self.actions:
            for a in self.actions:

                # fetch all the relevant 0-arity predicates and create formulas to set up the ground actions
                positive_preconds = [_get_str_as_tarski_grounded_formula(
                                        a[1:-1], lang) for a in a.positive_preconditions]
                # create a set of negative preconditions
                negative_preconds = [CompoundFormula(Connective.Not,
                                                     _get_str_as_tarski_grounded_formula(a[1:-1], lang),)
                                                    for a in a.negative_preconditions]

                precond_list = positive_preconds + negative_preconds
                if len(precond_list) == 1:
                    preconds = precond_list[0]
                elif len(precond_list) == 0:
                    preconds = top # always true
                else:
                    preconds = CompoundFormula(Connective.And, precond_list,)



                adds = [lang.get(f"{e.replace(' ', '_')[1:-1]}")() for e in a.add_effects] #todo validate on different
                dels = [lang.get(f"{e.replace(' ', '_')[1:-1]}")() for e in a.delete_effects]
                effects = [fs.AddEffect(e) for e in adds]
                effects.extend([fs.DelEffect(e) for e in dels])
                # set up action
                problem.action(
                    name=a.details()
                    .replace("(", "")
                    .replace(")", "")
                    .replace(" ", "_"),
                    parameters=[],
                    precondition=preconds,
                    effects=effects,)

        # create empty init and goal
        problem.init = tarski.model.create(lang)
        problem.goal = land()
        # write to files
        writer = iofs.FstripsWriter(problem)
        writer.write(domain_filename, problem_filename)

    # TODO complete
    # @classmethod
    # def _from_json(cls, data: dict):
    #     actions = set(map(_deserialize, data["actions"]))
    #     return cls(set(data["fluents"]), actions)

    # TODO complete
    # @staticmethod
    # def deserialize(string: str):
    #     """Deserializes a json string into a Model.
    #
    #     Args:
    #         string (str):
    #             The json string representing a model.
    #
    #     Returns:
    #         A Model object matching the one specified by `string`.
    #     """
    #     return Model._from_json(loads(string))

# TODO finish
    # @classmethod
    # def _from_json(cls, data: dict):
    #     actions = set(map(LearnedAction._deserialize, data["actions"]))
    #     return cls(set(data["fluents"]), actions)

from typing import Set, Union
from json import loads, dumps
from ..utils import ComplexEncoder
from .learned_action import LearnedAction
from ..trace import Fluent


class Model:
    """Action model.

    An action model representing a planning domain. The characteristics of the
    model are dependent on the extraction technique used to obtain the model.

    Attributes:
        fluents (set):
            The set of fluents in the domain.
        actions (set):
            The set of actions in the domain. Actions include their
            preconditions, add effects, and delete effects. The nature of the
            action attributes characterize the model.
    """

    def __init__(self, fluents: Set[Union[str, Fluent]], actions: Set[LearnedAction]):
        """Initializes a Model with a set of fluents and a set of actions.

        Args:
            fluents (set):
                The set of fluents in the model.
            actions (set):
                The set of actions in the model.
        """
        self.fluents = fluents
        self.actions = actions

    def __eq__(self, other):
        if not isinstance(other, Model):
            return False
        self_fluent_type, other_fluent_type = type(list(self.fluents)[0]), type(
            list(other.fluents)[0]
        )
        if self_fluent_type == other_fluent_type:
            return self.fluents == other.fluents and self.actions == other.actions
        if self_fluent_type == str:
            return set(map(lambda f: str(f), other.fluents)) == self.fluents
        if other_fluent_type == str:
            return set(map(lambda f: str(f), self.fluents)) == other.fluents

    def details(self):
        # Set the indent width
        indent = " " * 2
        string = "Model:\n"
        # Map fluents to a comma separated string of the fluent names
        try:
            string += f"{indent}Fluents: {', '.join(self.fluents)}\n"
        except TypeError:
            string += f"{indent}Fluents: {', '.join(map(str,self.fluents))}\n"

        # Map the actions to a summary of their names, preconditions, add
        # effects and delete effects
        string += f"{indent}Actions:\n"
        for line in self._get_action_details().splitlines():
            string += f"{indent * 2}{line}\n"
        return string

    def _get_action_details(self):
        # Set the indent width
        indent = " " * 2
        details = ""
        for action in self.actions:
            details += action.details() + ":\n"
            details += f"{indent}precond:\n"
            for f in action.precond:
                details += f"{indent * 2}{f}\n"
            details += f"{indent}add:\n"
            for f in action.add:
                details += f"{indent * 2}{f}\n"
            details += f"{indent}delete:\n"
            for f in action.delete:
                details += f"{indent * 2}{f}\n"

        return details

    def serialize(self, filepath: str = None):
        """Serializes the model into a json string.

        Args:
            filepath (str):
                Optional; If supplied, the json string will be written to the
                filepath.

        Returns:
            A string in json format representing the model.
        """

        serial = dumps(self._serialize(), cls=ComplexEncoder)
        if filepath is not None:
            with open(filepath, "w") as fp:
                fp.write(serial)
        return serial

    def _serialize(self):
        return dict(fluents=list(self.fluents), actions=list(self.actions))

    @staticmethod
    def deserialize(string: str):
        """Deserializes a json string into a Model.

        Args:
            string (str):
                The json string representing a model.

        Returns:
            A Model object matching the one specified by `string`.
        """
        return Model._from_json(loads(string))

    @classmethod
    def _from_json(cls, data: dict):
        actions = set(map(LearnedAction._deserialize, data["actions"]))
        return cls(set(data["fluents"]), actions)

from json import dump, dumps, loads
from ..trace import Fluent, Action
from . import ModelAction
from typing import Set


class Model:
    """Action model.

    An action model representing a planning problem. The characteristics of the
    model are dependent on the extraction technique used to obtain the model.

    Attributes:
        fluents (set):
            The set of fluents in the problem.
        actions (set):
            The set of actions in the problem. Actions include their
            preconditions, add effects, and delete effects. The nature of the
            action attributes characterize the model.
    """

    def __init__(self, fluents: Set[Fluent], actions: Set[ModelAction]):
        """Initializes a Model with a set of fluents and a set of actions.

        Args:
            fluents (set):
                The set of fluents in the model.
            actions (set):
                The set of actions in the model.
        """
        self.fluents = fluents
        self.actions = actions

    def __str__(self):
        # Set the indent width
        indent = " " * 2
        string = "Model:\n"
        # Map fluents to a comma separated string of the fluent names
        string += f"{indent}Fluents: {', '.join(map(str, self.fluents))}\n"
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
            details += str(action) + ":\n"
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
        if filepath is not None:
            with open(filepath, "w") as fp:
                dump(self, fp=fp, indent=2, default=lambda o: o.__dict__)

        # BROKEN
        return dumps(self, indent=2, default=lambda o: o.__dict__)

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
        fluents = set(map(Fluent.from_json, data["fluents"]))
        actions = set(map(ModelAction.from_json, data["actions"]))
        return cls(fluents, actions)

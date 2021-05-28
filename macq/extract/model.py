from json import dump, dumps, loads
from typing import List
from ..trace import Fluent, Action


class Model:
    """
    A Model object represents a planning model. Contains information about the
    fluents, actions, initial state, and goal of a problem.
    """

    def __init__(self, fluents: List[Fluent], actions: List[Action]):
        """
        Creates a Model object. This stores a list of fluents and actions that
        represent a planning model.

        Attributes
        ----------
        fluents : list
            The list of `Fluent` objects.
        actions : list
            The list of `Action` objects.
        """
        self.fluents = fluents
        self.actions = actions

    def __str__(self):
        string = "Model:\n"
        indent = " " * 2
        string += f"{indent}Fluents: {', '.join(map(str, self.fluents))}\n"
        string += f"{indent}Actions:\n"
        for line in self._get_action_details().splitlines():
            string += f"{indent * 2}{line}\n"
        return string

    def _get_action_details(self):
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
        """
        Serializes the model into a json string. If a filepath is supplied,
        the string is also saved to that file.

        Arguments
        ---------
        filepath : str
            The file to save the json object to.

        Returns
        -------
        JSON representation of the model object : str
        """
        if filepath is not None:
            with open(filepath, "w") as fp:
                dump(self, fp=fp, indent=2, default=lambda o: o.__dict__)

        return dumps(self, indent=2, default=lambda o: o.__dict__)

    @staticmethod
    def deserialize(string):
        """
        Deserializes a json string into a Model object.

        Arguments
        ---------
        string : str
            The json string representing a model.

        Returns
        -------
        The Model object represented by the string : Model
        """
        return Model.from_json(loads(string))

    @classmethod
    def from_json(cls, data: dict):
        """
        Converts a json object to a Model object.

        Arguments
        ---------
        data : dict
            The json object.

        Returns
        -------
        The Model corresponding model object : Model
        """
        fluents = list(map(Fluent.from_json, data["fluents"]))
        actions = list(map(Action.from_json, data["actions"]))
        return cls(fluents, actions)

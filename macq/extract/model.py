from json import dump, dumps
from typing import List
from ..trace import Fluent, Action, State


class Model:
    """
    A Model object represents a planning model. Contains information about the
    fluents, actions, initial state, and goal of a problem.
    """

    def __init__(
        self,
        fluents: List[Fluent],
        actions: List[Action],
        initial_state: State,
        goal: State,
    ):
        self.fluents = fluents
        self.actions = actions
        self.initial_state = initial_state
        self.goal = goal

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

    def unserialize(self):
        pass

    def to_pddl(self):
        pass

from typing import List
from tarski.fstrips.action import PlainOperator


class Plan:
    """A Plan.

    Holds a list of tarski `PlainOperator`s that correspond to actions that can be used
    to generate traces. Also includes functionality to read/write plans to/from IPC files.

    Attributes:
        actions (List[PlainOperator]):
            The list of actions that make up the plan.
    """

    def __init__(self, actions: List[PlainOperator]):
        """Creates a Plan by instantiating it with the list of actions (of tarski type `PlainOperator`).

        Args:
            actions (List[PlainOperator]):
                The list of actions that make up the plan.
        """
        self.actions = actions

    def write_to_file(self, filename: str):
        """Writes the plan to the provided file in IPC format.

        Args:
            filename (str):
                The name of the file to write the plan to.
        """
        with open(filename, "w") as f:
            f.write(str(self) + f"\n; cost = {len(self.actions)} (unit cost)")

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        string = [str(act) for act in self.actions]
        # convert to IPC format
        for i in range(len(string)):
            string[i] = string[i].replace("(", " ").replace(",", "")
            string[i] = "(" + string[i]
        return "\n".join(string)

    def __eq__(self, other):
        return isinstance(other, Plan) and self.actions == other.actions

from typing import List

from pddl.action import Action


class Plan:
    """A Plan.

    Holds a list of ground actions that can be used to generate traces. Also includes
    functionality to read/write plans to/from IPC files.

    Attributes:
        actions (List[Action]):
            The list of ground actions that make up the plan.
    """

    def __init__(self, actions: List[Action]):
        """Creates a Plan by instantiating it with the list of ground actions.

        Args:
            actions (List[Action]):
                The list of ground actions that make up the plan.
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
        # IPC format
        return "\n".join(
            "(" + " ".join([str(act.name), *[str(t.name) for t in act.parameters]]) + ")"
            for act in self.actions
        )

    def __eq__(self, other):
        return isinstance(other, Plan) and self.actions == other.actions

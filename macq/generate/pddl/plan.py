from typing import List
from tarski.fstrips.action import PlainOperator


class Plan:
    def __init__(self, actions: List[PlainOperator]):
        self.actions = actions

    def write_to_file(self, filename: str):
        """Writes the plan to the provided file.

        Args:
            filename (str):
                The name of the file to write the plan to.
        """
        with open(filename, "w") as f:
            f.write("\n".join(act for act in self.actions))

    def __hash__(self):
        return hash(str(self))

    def __str__(self):
        return "\n".join(str(act) for act in self.actions)

    def __eq__(self, other):
        if isinstance(other, Plan):
            return self.actions == other.actions

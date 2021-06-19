from typing import List


class PlanningObject:
    """An object of a planning domain.

    Attributes:
        obj_type (str):
            The type of object in the problem domain.
            Example: "block".
        name (str):
            The name of the object.
            Example: "A"
    """

    def __init__(self, obj_type: str, name: str):
        """Initializes a PlanningObject with a type and a name.

        Args:
            obj_type (str):
                The type of object in the problem domain.
            name (str):
                The name of the object.
        """
        self.obj_type = obj_type
        self.name = name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, PlanningObject) and self.name == other.name

    def details(self):
        return " ".join([self.obj_type, self.name])

    @classmethod
    def from_json(cls, data):
        """Converts a json object to a PlanningObject."""
        return cls(**data)


class Fluent:
    """Fluents of a planning domain.

    Attributes:
        name (str):
            The name of the fluent.
            Example: "holding".
        objects (list):
            The objects this fluent applies to.
            Example: Block A.
    """

    def __init__(self, name: str, objects: List[PlanningObject]):
        """Initializes a Fluent with a name and a list of objects.

        Args:
            name (str):
                The name of the fluent.
            objects (list):
                The objects this fluent applies to.
        """
        self.name = name
        self.objects = objects

    def __hash__(self):
        # Order of objects is important!
        return hash(self.details())

    def details(self):
        return f"{self.name} {' '.join([o.details() for o in self.objects])}"

    def __eq__(self, other):
        return (
            isinstance(other, Fluent)
            and self.name == other.name
            and self.objects == other.objects
        )

    @classmethod
    def from_json(cls, data):
        """Converts a json object to a Fluent."""
        objects = list(map(PlanningObject.from_json, data["objects"]))
        return cls(data["name"], objects)

from .object_type import ObjectType

class PlanningObject:
    """An object of a planning domain.

    Attributes:
        name (str):
            the object's name.
        obj_type (str):
            The type of the object in the problem domain.
            Example: "block".

    """

    def __init__(self, name: str, obj_type: ObjectType):
        """Initializes a PlanningObject with a type and a name.

        Args:
            name (str):
                The name of the object.
            obj_type (str):
                The type of the object in the problem domain.
        """
        self.name = name
        self.obj_type = obj_type


    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, PlanningObject) and self.name == other.name

    def details(self):
        return " ".join([self.obj_type.type_name, self.name])

    def __repr__(self):
        return self.details()

    def _serialize(self):
        return self.details()
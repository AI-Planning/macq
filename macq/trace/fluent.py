from typing import List


class CustomObject:
    def __init__(self, obj_type: str, name: str):
        self.obj_type = obj_type
        self.name = name

    def __str__(self):
        string = "Object:\n"
        string += f"  name: {self.name}\n"
        string += f"  type: {self.obj_type}"
        return string

    @classmethod
    def from_json(cls, data):
        """
        Converts a json object to a Custom object.

        Arguments
        ---------
        data : dict
            The json object.

        Returns
        -------
        The corresponding Custom object : CustomObject
        """
        return cls(**data)


class Fluent:
    def __init__(self, name: str, objects: List[CustomObject]):
        """
        Class to handle a predicate and the objects it is applied to.

        Arguments
        ---------
        name : str
            The name of the predicate.
        objects : list
            The list of objects this predicate applies to.
        value : bool
            The value of the fluent (true or false)
        """
        self.name = name
        self.objects = objects

    def __str__(self):
        string = "Fluent:\n"
        string += f"  name: {self.name}\n"
        string += f"  objects:\n"
        for obj in self.objects:
            for line in str(obj).split("\n"):
                string += f"    {line}\n"
        return string.rstrip()

    def __hash__(self):
        return hash(str(self))

    @classmethod
    def from_json(cls, data):
        """
        Converts a json object to a Fluent object.

        Arguments
        ---------
        data : dict
            The json object.

        Returns
        -------
        The corresponding Fluent object : Fluent
        """
        objects = list(map(CustomObject.from_json, data["objects"]))
        return cls(data["name"], objects)

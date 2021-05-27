from typing import List


class CustomObject:
    def __init__(self, obj_type: str, name: str):
        self.obj_type = obj_type
        self.name = name

    def __str__(self):
        return self.name

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
        """
        self.name = name
        self.objects = objects

    def __str__(self):
        return self.name

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

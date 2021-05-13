from typing import List


class CustomObject:
    def __init__(self, obj_type, name):
        self.obj_type = obj_type
        self.name = name


class Fluent:
    def __init__(self, name: str, objects: List[CustomObject], value: bool):
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
        self.value = value


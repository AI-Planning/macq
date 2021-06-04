from typing import List


class CustomObject:
    def __init__(self, obj_type: str, name: str):
        self.obj_type = obj_type
        self.name = name

    def __repr__(self):
        string = "Type: " + self.obj_type + ", Name: " + self.name
        return string

    def __eq__(self, other):
        return isinstance(other, CustomObject) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class Fluent:
    def __init__(self, name: str, objects: List[CustomObject], value: bool = True):
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

    def __repr__(self):
        string = "Fluent with Name: " + self.name + "\nObjects:\n"
        for obj in self.objects:
            string += str(obj) + "\n"
        string += "Value: " + str(self.value)
        return string

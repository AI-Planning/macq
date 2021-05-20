from typing import List

class CustomObject:
    def __init__(self, obj_type: str, name: str):
        self.obj_type = obj_type
        self.name = name
    def __repr__(self):
        string = "Type: " + self.obj_type + ", Name: " + self.name
        return string
    def __eq__(self, other):
        if isinstance(other, CustomObject):
            return self.name == other.name and self.obj_type == other.obj_type
        else:
            return False


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
    def __repr__(self):
        string = "Fluent with Name: " + self.name + "\nObjects:\n"
        for obj in self.objects:
            string += str(obj) + "\n"
        string += "Value: " + str(self.value)
        return string



from dataclasses import dataclass

from .object_type import ObjectType

@dataclass
class SignatureParameter:
    name: str
    object_type: ObjectType = None

    def __post_init__(self):
        # Initialize with the default ObjectType if None is provided
        if self.object_type is None:
            self.object_type = ObjectType("object")

    def __str__(self):
        return f"{self.name}"

    def details(self):
        return f"{self.name} {self.object_type}"

    def __hash__(self):
        return hash(str(self))

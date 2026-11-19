from dataclasses import dataclass, field

from .object_type import ObjectType


@dataclass(frozen=True)
class SignatureParameter:
    """A named, typed parameter of an action or predicate."""

    name: str
    object_type: ObjectType = field(default_factory=ObjectType)

    def __str__(self):
        return self.name

    def details(self):
        return f"{self.name} {self.object_type}"

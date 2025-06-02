from typing import List
from ..signature_parameter import SignatureParameter

class LiftedFluent:
    """Represents a lifted fluent, which is a structural element often used in
    planning domains to describe state properties over objects and their
    relationships.

    A lifted fluent is characterized by its name and parameters. It can be
    hashed, printed as a string, or compared with other instances based on
    its name and parameters.

    Attributes:
        name (str): The name of the lifted fluent, indicating its identity
            in the planning domain.
        parameters (List[SignatureParameter]): A list of parameters that
            define the schema of the lifted fluent.
    """
    name: str
    parameters: List[SignatureParameter]

    def __init__(self, name: str, parameters: List[SignatureParameter]):
        self.name = name
        self.parameters = parameters

    def __hash__(self):
        return hash(self.name) + hash(tuple(self.parameters))

    def __str__(self):
        return self.name + ' '.join(map(str,self.parameters))

    def  details(self):
        return str(self)

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        return isinstance(other, LiftedFluent) and hash(self) == hash(other)

    def _serialize(self):
        return self.details()
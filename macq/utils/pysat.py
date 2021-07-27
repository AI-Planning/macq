from typing import List, Tuple, Dict, Hashable
from pysat.formula import WCNF
from nnf import And, Or, Var


class NotCNF(Exception):
    def __init__(self, clauses):
        self.clauses = clauses
        super().__init__(f"Cannot convert a non CNF formula to WCNF")


def _encode(clauses: And[Or[Var]]) -> Tuple[List[List[int]], Dict[int, Hashable]]:
    decode = dict(enumerate(clauses.vars(), start=1))
    encode = {v: k for k, v in decode.items()}
    encoded = [
        [encode[var.name] if var.true else -encode[var.name] for var in clause]
        for clause in clauses
    ]

    return encoded, decode


def to_wcnf(
    clauses: And[Or[Var]], weights: List[int]
) -> Tuple[WCNF, Dict[int, Hashable]]:
    """Converts a python-nnf CNF formula to a pysat WCNF."""
    # if not clauses.is_CNF():
    #     raise NotCNF(clauses)
    encoded, decode = _encode(clauses)
    wcnf = WCNF()
    wcnf.extend(encoded, weights)
    return wcnf, decode

from typing import List, Tuple, Dict, Hashable
from pysat.formula import WCNF
from nnf import And, Or, Var


class NotCNF(Exception):
    def __init__(self, clauses):
        self.clauses = clauses
        super().__init__(f"Cannot convert a non CNF formula to WCNF")

def encode_dict(clauses: And[Or[Var]], start: int = 1):# -> Tuple[List[List[int]], Dict[int, Hashable]]:
    decode = dict(enumerate(clauses.vars(), start=start))
    encode = {v: k for k, v in decode.items()}
    return decode, encode

def encode(clauses: And[Or[Var]], encode):# -> Tuple[List[List[int]], Dict[int, Hashable]]:
    encoded = [
        [encode[var.name] if var.true else -encode[var.name] for var in clause]
        for clause in clauses
    ]
    return encoded

def to_wcnf(
    soft_clauses: And[Or[Var]], hard_clauses: And[Or[Var]], weights: List[int]
) -> Tuple[WCNF, Dict[int, Hashable]]:
    """Converts a python-nnf CNF formula to a pysat WCNF."""
    soft_decode, soft_encode = encode_dict(soft_clauses)
    hard_decode, hard_encode = encode_dict(hard_clauses, start = len(soft_decode) + 1)
    wcnf = WCNF()
    wcnf.extend(encode(soft_clauses, soft_encode), weights)
    wcnf.extend(encode(hard_clauses, hard_encode))
    decode = {**soft_decode, **hard_decode}
    return wcnf, decode
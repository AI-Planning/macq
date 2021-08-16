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

    # WARNING: debugging
    for k in encode.keys():
        if "holding" in str(k) and "del" in str(k) and "put-down" in str(k):
            global H_DEL_PD
            H_DEL_PD = encode[k]
        if "holding" in str(k) and "del" in str(k) and "(stack" in str(k):
            global H_DEL_S
            H_DEL_S = encode[k]
        if "holding" in str(k) and "add" in str(k) and "pick-up" in str(k):
            global H_ADD_PU
            H_ADD_PU = encode[k]
        if "on object" in str(k) and "del" in str(k) and "pick-up" in str(k):
            global O_DEL_PU
            O_DEL_PU = encode[k]
        if "on object" in str(k) and "add" in str(k) and "unstack" in str(k):
            global O_ADD_US
            O_ADD_US = encode[k]
        if "ontable" in str(k) and "add" in str(k) and "unstack" in str(k):
            global OT_ADD_US
            OT_ADD_US = encode[k]
    # WARNING: debugging

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

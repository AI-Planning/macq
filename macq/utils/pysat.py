from typing import List, Tuple, Dict, Hashable
from pysat.formula import WCNF
from nnf import And, Or, Var


def get_encoding(
    clauses: And[Or[Var]], start: int = 1
) -> Tuple[Dict[Hashable, int], Dict[int, Hashable]]:
    decode = dict(enumerate(clauses.vars(), start=start))
    encode = {v: k for k, v in decode.items()}
    return encode, decode


def encode(clauses: And[Or[Var]], encode: Dict[Hashable, int]) -> List[List[int]]:
    encoded = [
        [encode[var.name] if var.true else -encode[var.name] for var in clause]
        for clause in clauses
    ]
    return encoded


def to_wcnf(
    soft_clauses: And[Or[Var]], weights: List[int], hard_clauses: And[Or[Var]] = None
) -> Tuple[WCNF, Dict[int, Hashable]]:
    """Converts a python-nnf CNF formula to a pysat WCNF."""
    wcnf = WCNF()
    soft_encode, decode = get_encoding(soft_clauses)
    encoded = encode(soft_clauses, soft_encode)
    wcnf.extend(encoded, weights)

    if hard_clauses:
        hard_encode, hard_decode = get_encoding(hard_clauses, start=len(decode) + 1)
        decode.update(hard_decode)
        encoded = encode(hard_clauses, hard_encode)
        wcnf.extend(encoded)

    return wcnf, decode

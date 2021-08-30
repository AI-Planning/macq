from typing import List, Tuple, Dict, Hashable
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
from nnf import And, Or, Var


def get_encoding(
    clauses: And[Or[Var]], start: int = 1
) -> Tuple[Dict[Hashable, int], Dict[int, Hashable]]:
    """Maps NNF clauses to pysat clauses and vice-versa.

    Args:
        clauses (And[Or[Var]]):
            NNF clauses (in conjunctive normal form) to be mapped to pysat clauses.
        start (int):
            Optional; The number to start the mapping from. Defaults to 1.

    Returns:
        Tuple[Dict[Hashable, int], Dict[int, Hashable]]:
            The encode mapping (NNF to pysat), and the decode mapping (pysat to NNF).
    """
    decode = dict(enumerate(clauses.vars(), start=start))
    encode = {v: k for k, v in decode.items()}
    return encode, decode


def encode(clauses: And[Or[Var]], encode: Dict[Hashable, int]) -> List[List[int]]:
    """Encodes NNF clauses into pysat clauses.

    Args:
        clauses (And[Or[Var]]):
            NNF clauses (in conjunctive normal form) to be converted to pysat clauses.
        encode (Dict[Hashable, int]):
            The encode mapping to apply to the NNF clauses.

    Returns:
        List[List[int]]:
            The pysat encoded clauses.
    """
    encoded = [
        [encode[var.name] if var.true else -encode[var.name] for var in clause]
        for clause in clauses
    ]
    return encoded


def to_wcnf(
    soft_clauses: And[Or[Var]], weights: List[int], hard_clauses: And[Or[Var]] = None
) -> Tuple[WCNF, Dict[int, Hashable]]:
    """Builds a pysat weighted CNF theory from pysat clauses.

    Args:
        soft_clauses (And[Or[Var]]):
            The soft clauses (NNF clauses, in CNF) for the WCNF theory.
        weights (List[int]):
            The weights to associate with the soft clauses.
        hard_clauses (And[Or[Var]]):
            Optional; Hard clauses (unweighted) to add to the WCNF theory.

    Returns:
        Tuple[WCNF, Dict[int, Hashable]]:
            The WCNF theory, and the decode mapping to convert the pysat vars back to NNF.
    """
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

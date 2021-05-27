from enum import Enum, auto

class Configure:
    class determinism(Enum):
        FULLY = auto()
        NON = auto()
        PROB = auto()
    class observability(Enum):
        FULLY = auto()
        PARTIAL = auto()
        RANDOM = auto()
    class rationality(Enum):
        YES = auto()
        NO = auto()
        BOUNDED = auto()
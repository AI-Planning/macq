
from random import shuffle
from ..trace import State

def extract_fluent_subset(self, fluents: State, percent: float):
    num_new_f = int(len(fluents) * (percent))

    # shuffle keys and take an appropriate subset of them
    extracted_f = list(fluents)
    shuffle(extracted_f)
    return extracted_f[:num_new_f]
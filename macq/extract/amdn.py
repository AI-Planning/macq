import macq.extract as extract
from .model import Model
from ..trace import ObservationLists
from ..observation import NoisyPartialDisorderedParallelObservation

class AMDN:
    def __new__(cls, obs_lists: ObservationLists):
        """Creates a new Model object.

        Args:
            obs_lists (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if obs_lists.type is not NoisyPartialDisorderedParallelObservation:
            raise extract.IncompatibleObservationToken(obs_lists.type, AMDN)

        # TODO:
        # iterate through all tokens and create two base sets for all actions and propositions; store as attributes
        # iterate through all pairs of parallel action sets and create a dictionary of the probability of ax and ay being disordered -
        # (this will make it easy and efficient to refer to later, and prevents unnecessary recalculations). store as attribute
        # also create a list of all <a, r> tuples, store as attribute

        #return Model(fluents, actions)

    def __build_disorder_constraints(self):
        # TODO:
        # iterate through all pairs of parallel action sets
        # for each pair, iterate through all possible action combinations
        # calculate the probability of the actions being disordered (p)
        # for each action combination, iterate through all possible propositions
        # for each action x action x proposition combination, enforce the following constraint if the actions are ordered:
        # enforce all [constraint 1] with weight (1 - p) x wmax

        # likewise, enforce the following constraint if the actions are disordered:
        # enforce all [constraint 2] with weight p x wmax
        pass

    def __build_hard_parallel_constraints(self):
        # TODO:
        # iterate through the list of <a, r> tuples
        # for each action x proposition pair, enforce the two hard constraints with weight wmax
        pass

    def __build_soft_parallel_constraints(self):
        # TODO:
        # iterate through all parallel action sets
        # within each parallel action set, iterate through the same action set again to compare
        # each action to every other action in the set; assuming none are disordered
        # enforce all [constraint 4] with weight (1 - p) x wmax

        # then, iterate through all pairs of action sets
        # assuming the actions are disordered, check ay against EACH action in ax, for each pair
        # enforce all [constraint 5] with weight p x wmax
        pass

    def __build_parallel_constraints(self):
        # TODO:
        # call the above two functions
        pass

    def __build_noise_constraints(self):
        # TODO:
        # iterate through all <a, r> tuples
        # for each <a, r> tuple: iterate through each step over ALL the plan traces
        # count the number of occurrences; if higher than the user-provided parameter delta,
        # store this tuple as a dictionary entry in a list of dictionaries (something like 
        # [{"action and proposition": <a, r>, "occurrences of r:" 5}]).
        # after all iterations are through, iterate through all the tuples in this dictionary,
        # and set [constraint 6] with the calculated weight.
        # TODO: Ask - what "occurrences of all propositions" refers to - is it the total number of steps...?
        
        # store the initial state s0
        # iterate through every step in the plan trace
        # at each step, check all the propositions r in the current state
        # if r is not in s0, enforce [constraint 7] with the calculated weight
        # TODO: Ask - what happens when you find the first r? I assume you keep iterating through the rest of the trace,
        # continuing the process with different propositions? Do we still count the occurrences of each proposition through
        # the entire trace to use when we calculate the weight?

        # [constraint 8] is almost identical to [constraint 6]. Watch the order of the tuples. 

        pass

    def __solve_constraints(self):
        # TODO:
        # call the MAXSAT solver
        pass

    def __convert_to_model(self):
        # TODO:
        # convert the result to a Model
        pass
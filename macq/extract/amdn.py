from nnf.operators import implies
import macq.extract as extract
from nnf import Var, And, Or
from .model import Model
from ..trace import ObservationLists
from ..observation import NoisyPartialDisorderedParallelObservation

def __set_precond(r, act):
    return Var(r + " is a precondition of " + act.name)

def __set_del(r, act):
    return Var(r + " is deleted by " + act.name)

def __set_add(r, act):
    return Var(r + " is added by " + act.name)

# for easier reference
pre = __set_precond
add = __set_add
delete = __set_del

class AMDN:
    def __init__(self, obs_lists: ObservationLists):
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
        self.actions = obs_lists.actions

        # iterate through all pairs of parallel action sets and create a dictionary of the probability of ax and ay being disordered -
        # (this will make it easy and efficient to refer to later, and prevents unnecessary recalculations). store as attribute
        # also create a list of all <a, r> tuples, store as attribute
        # get user values (TODO: ask: wmax is a user value...?)

        #return Model(fluents, actions)

    def _build_disorder_constraints(self):
        # TODO:
        # iterate through all pairs of parallel action sets
        for i in range(len(self.par_act_sets) - 1):
            # for each pair, iterate through all possible action combinations
            for act_x in self.par_act_sets[i]:
                for act_y in self.par_act_sets[i + 1]:
                # TODO: calculate the probability of the actions being disordered (p)
                    # for each action combination, iterate through all possible propositions
                    # TODO: calculate weights
                    for r in self.propositions:
                        # enforce the following constraint if the actions are ordered with weight (1 - p) x wmax:
                        constraint1 = Or([
                            And([pre(r, act_x), ~delete(r, act_x), delete(r, act_y)]),
                            And([add(r, act_x), pre(r, act_y)]),
                            And([add(r, act_x), delete(r, act_y)]),
                            And([delete(r, act_x), add(r, act_y)])
                            ])
                        # likewise, enforce the following constraint if the actions are disordered with weight p x wmax:
                        constraint2 = Or([
                            And([pre(r, act_y), ~delete(r, act_y), delete(r, act_x)]),
                            And([add(r, act_y), pre(r, act_x)]),
                            And([add(r, act_y), delete(r, act_x)]),
                            And([delete(r, act_y), add(r, act_x)])
                            ])

    def __build_hard_parallel_constraints(self):
        # for easier reference
        pre = self.__set_precond
        add = self.__set_add
        delete = self.__set_del

        # iterate through the list of <a, r> tuples
        for tup in self.act_prop_cross_prod:
            act = tup[0]
            r = tup[1]
            # for each action x proposition pair, enforce the two hard constraints with weight wmax
            constraint1 = implies(add(r, act), ~pre(r, act))
            constraint2 = implies(delete(r, act), pre(r, act))
            # TODO: use weight wmax

    def __build_soft_parallel_constraints(self):
        constraints_4 = set()
        constraints_5 = set()
        # iterate through all parallel action sets
        for i in range(len(self.par_act_sets)):        
            # within each parallel action set, iterate through the same action set again to compare
            # each action to every other action in the set; setting constraints assuming actions are not disordered
            for act_x in self.par_act_sets[i]:
                for act_x_prime in self.par_act_sets[i]:
                    if act_x != act_x_prime:
                        # iterate through all propositions
                        for r in self.propositions:
                            # equivalent: if r is in the add or delete list of an action in the set, that implies it 
                            # can't be in the add or delete list of any other action in the set
                            constraints_4.add(implies(Or([add(r, act_x)], delete(r, act_x)), ~Or([add(r, act_x_prime)], delete(r, act_x_prime))))
        # TODO: enforce all [constraint 4] with weight (1 - p) x wmax

        # then, iterate through all pairs of parallel action sets
        for i in range(len(self.par_act_sets) - 1):
            # for each pair, compare every action in act_y to every action in act_x_prime; setting constraints
            # assuming actions are disordered
            for act_y in self.par_act_sets[i + 1]:
                for act_x_prime in self.par_act_sets[i]:
                    if act_y != act_x_prime:
                        # iterate through all propositions and similarly set the constraint
                        for r in self.propositions:
                            constraints_5.add(implies(Or([add(r, act_y)], delete(r, act_y)), ~Or([add(r, act_x_prime)], delete(r, act_x_prime))))      
        # TODO: enforce all [constraint 5] with weight p x wmax

    def __build_parallel_constraints(self):
        self.__build_hard_parallel_constraints()
        self.__build_soft_parallel_constraints()

    def _build_noise_constraints(self):
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

    def _solve_constraints(self):
        # TODO:
        # call the MAXSAT solver
        pass

    def _convert_to_model(self):
        # TODO:
        # convert the result to a Model
        pass
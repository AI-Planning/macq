from dataclasses import dataclass
from math import exp
from numpy import dot
from random import random
from typing import Callable, Type, Set, List
from . import TraceList, Step, Action, PartialState, State
from ..observation import Observation, ObservedTraceList


@dataclass
class ActionPair:
    """dataclass that allows a pair of actions to be referenced regardless of order
    (that is, {action1, action2} is equivalent to {action2, action1}.)
    """

    actions: Set[Action]

    def tup(self):
        actions = list(self.actions)
        return (actions[0], actions[1])

    def __hash__(self):
        # order of actions is irrelevant; {a_x, a_y} == {a_y, a_x}
        sum = 0
        for a in self.actions:
            sum += hash(a.details())
        return sum

    def __repr__(self):
        string = ""
        for a in self.actions:
            string += a.details() + ", "
        return string[:-1]


def default_theta_vec(k: int):
    """Generate the default theta vector to be used in the calculation that extracts the probability of
    actions being disordered; used to "weight" the features.

    Args:
        k (int):
            The size of the vector/the denominator of the weight to be used

    Returns:
        The default theta vector.
    """
    return [(1 / k)] * k


def objects_shared_feature(act_x: Action, act_y: Action):
    """Corresponds to default feature 1 from the AMDN paper.

    Args:
        act_x (Action):
            The first action to be compared.
        act_y (Action):
            The second action to be compared.

    Returns:
        The number of objects shared by the two actions.
    """
    num_shared = 0
    for obj in act_x.obj_params:
        for other_obj in act_y.obj_params:
            if obj == other_obj:
                num_shared += 1
    return num_shared


def num_parameters_feature(act_x: Action, act_y: Action):
    """Corresponds to default feature 2 from the AMDN paper.

    Args:
        act_x (Action):
            The first action to be compared.
        act_y (Action):
            The second action to be compared.

    Returns:
        1 if the actions share the same number of parameters, 0 otherwise.
    """
    return 1 if len(act_x.obj_params) == len(act_y.obj_params) else 0


def _decision(probability: float):
    """Makes a decision based on the given probability.

    Args:
        probability (float):
            The probability used to make the decision.

     Returns:
        The (bool) decision made.
    """
    return random() < probability


class DisorderedParallelActionsObservationLists(ObservedTraceList):
    """Alternate ObservationLists type that enforces appropriate actions to be disordered and/or parallel.
    Inherits the base ObservationLists class.

    The default feature functions and theta vector described in the AMDN paper are available for use in this module.

    Attributes:
        observations (List[List[Token]]):
            The trace list converted to a list of lists of tokens.
        type (Type[Observation]):
            The type of token to be used.
        all_par_act_sets (List[List[Set[Action]]]):
            Holds the parallel action sets for all traces.
        all_states (List(List[State])):
            Holds the relevant states for all traces. Note that these are RELATIVE to the parallel action sets and only
            contain the states between the sets.
        features (List[Callable]):
            The list of functions to be used to create the feature vector.
        learned_theta (List[float]):
            The supplied theta vector.
        actions (List[Action]):
            The list of all actions used in the traces given (no duplicates).
        propositions (Set[Fluent]):
            The set of all fluents.
        cross_actions (List[ActionPair]):
            The list of all possible `ActionPairs`.
        denominator (float):
            The value used for the denominator in all probability calculations (stored so it doesn't need to be recalculated
            each time).
        probabilities (Dict[ActionPair, float]):
            A dictionary that contains a mapping of each possible `ActionPair` and the probability that the actions
            in them are disordered.
    """

    def __init__(
        self,
        traces: TraceList,
        Token: Type[Observation],
        features: List[Callable],
        learned_theta: List[float],
        **kwargs
    ):
        """AI is creating summary for __init__

        Args:
            traces (TraceList):
                The traces to generate tokens from.
            Token (Type[Observation]):
                The Token type to be used.
            features (List[Callable]):
                The list of functions to be used to create the feature vector.
            learned_theta (List[float]):
                The supplied theta vector.
            **kwargs:
                Any extra arguments to be supplied to the Token __init__.
        """
        self.observations = []
        self.type = Token
        self.all_par_act_sets = []
        self.all_states = []
        self.features = features
        self.learned_theta = learned_theta
        actions = {step.action for trace in traces for step in trace if step.action}
        # cast to list for iteration purposes
        self.actions = list(actions)
        # set of all fluents
        self.propositions = {
            f for trace in traces for step in trace for f in step.state.fluents
        }
        # create |A| (action x action set, no duplicates)
        self.cross_actions = [
            ActionPair({self.actions[i], self.actions[j]})
            for i in range(len(self.actions))
            for j in range(i + 1, len(self.actions))
        ]
        self.denominator = self._calculate_denom()
        # dictionary that holds the probabilities of all actions being disordered
        self.probabilities = self._calculate_all_probabilities()
        self.tokenize(traces, Token, **kwargs)

    @staticmethod
    def _theta_dot_features_calc(f_vec: List[float], theta_vec: List[float]):
        """Calculate the dot product of the feature vector and the theta vector, then use that as an exponent
        for 'e'.

        Args:
            f_vec (List[float]):
                The feature vector.
            theta_vec (List[float]):
                The theta vector.

        Returns:
            The result of the calculation.
        """
        return exp(dot(f_vec, theta_vec))

    def _calculate_denom(self):
        """
        Calculates and returns the denominator used in probability calculations.
        """
        denominator = 0
        for combo in self.cross_actions:
            denominator += self._theta_dot_features_calc(
                self._get_f_vec(*combo.tup()), self.learned_theta
            )
        return denominator

    def _get_f_vec(self, act_x: Action, act_y: Action):
        """Returns the feature vector.

        Args:
        act_x (Action):
            The first action to be used in each feature function.
        act_y (Action):
            The second action to be used in each feature function.

        Returns:
            The full feature vector.
        """
        return [f(act_x, act_y) for f in self.features]

    def _calculate_probability(self, act_x: Action, act_y: Action):
        """Calculates the probability of two actions being disordered.

        Args:
            act_x (Action):
                The first action.
            act_y (Action):
                The second action.

        Returns:
            The probability of two actions being disordered.
        """
        # calculate the probability of two given actions being disordered
        f_vec = self._get_f_vec(act_x, act_y)
        numerator = self._theta_dot_features_calc(f_vec, self.learned_theta)
        return numerator / self.denominator

    def _calculate_all_probabilities(self):
        """Calculates the probabilities of all combinations of actions being disordered.

        Returns:
            A dictionary that contains a mapping of each possible `ActionPair` and the probability that the actions
            in them are disordered.
        """
        probabilities = {}
        # access all ActionPairs
        for combo in self.cross_actions:
            # calculate probability of act_x and act_y being disordered
            probabilities[combo] = self._calculate_probability(*combo.tup())
        return probabilities

    def _get_new_partial_state(self):
        """
        Return a PartialState with the fluents used in this observation, with each fluent set to None as default.
        """
        cur_state = PartialState()
        for f in self.propositions:
            cur_state[f] = None
        return cur_state

    def _update_partial_state(
        self, partial_state: PartialState, orig_state: State, action: Action
    ):
        """
        Update the provided PartialState with the fluents provided.
        """
        new_partial = partial_state.copy()
        effects = set([e for e in action.add] + [e for e in action.delete])
        for e in effects:
            new_partial[e] = orig_state[e]
        return new_partial

    def tokenize(self, traces: TraceList, Token: Type[Observation], **kwargs):
        """Main driver that handles the tokenization process.

        Args:
            traces (TraceList):
                The traces to generate tokens from.
            Token (Type[Observation]):
                The Token type to be used.
            **kwargs:
                Any extra arguments to be supplied to the Token __init__.
        """
        # build parallel action sets
        for trace in traces:
            par_act_sets = []
            states = []
            cur_par_act = set()
            cur_par_act_conditions = set()
            # add initial state
            states.append(trace[0].state)

            cur_state = self._get_new_partial_state()

            # last step doesn't have an action/just contains the state after the last action
            for i in range(len(trace)):
                a = trace[i].action
                if a:
                    a_conditions = set(
                        [p for p in a.precond]
                        + [e for e in a.add]
                        + [e for e in a.delete]
                    )
                    # if the action has any conditions in common with any actions in the previous parallel set (NOT parallel)
                    if a_conditions.intersection(cur_par_act_conditions) != set():
                        # add psi_k and s'_k to the final (ordered) lists of parallel action sets and states
                        par_act_sets.append(cur_par_act)
                        states.append(cur_state)
                        # reset the state
                        cur_state = self._get_new_partial_state()
                        # reset psi_k (that is, create a new parallel action set)
                        cur_par_act = set()
                        # reset the conditions
                        cur_par_act_conditions = set()
                    # add the action and state to the appropriate psi_k and s'_k (either the existing ones, or
                    # new/empty ones if the current action is NOT parallel with actions in the previous set of actions.)
                    cur_par_act.add(a)
                    cur_state = self._update_partial_state(
                        cur_state, trace[i + 1].state, trace[i].action
                    )
                    cur_par_act_conditions.update(a_conditions)
                # if on the last step of the trace, add the current set/state to the final result before exiting the loop
                if i == len(trace) - 1:
                    par_act_sets.append(cur_par_act)
                    states.append(cur_state)

            # generate disordered actions - do trace by trace
            # prevent going over sets twice
            for i in range(len(par_act_sets)):
                # prevent comparing the same sets
                for j in range(i + 1, len(par_act_sets)):
                    for act_x in par_act_sets[i]:
                        for act_y in par_act_sets[j]:
                            if act_x != act_y:
                                # get probability and divide by distance
                                prob = self.probabilities[
                                    ActionPair({act_x, act_y})
                                ] / (j - i)
                                if _decision(prob):
                                    par_act_sets[i].discard(act_x)
                                    par_act_sets[i].add(act_y)
                                    par_act_sets[j].discard(act_y)
                                    par_act_sets[j].add(act_x)

            self.all_par_act_sets.append(par_act_sets)
            self.all_states.append(states)
            tokens = []
            for i in range(len(par_act_sets)):
                for act in par_act_sets[i]:
                    tokens.append(
                        Token(
                            Step(state=states[i], action=act, index=i),
                            par_act_set_ID=i,
                            **kwargs
                        )
                    )
            # add the final token, with the final state but no action
            tokens.append(
                Token(
                    Step(state=states[-1], action=None, index=len(par_act_sets)),
                    par_act_set_ID=len(par_act_sets),
                    **kwargs
                )
            )
            self.append(tokens)

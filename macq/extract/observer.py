from typing import List, Set
from collections import defaultdict
import macq.extract as extract
from .model import Model
from ..trace import ObservationList, Action
from ..observation import Observation, IdentityObservation


class Observer:
    """Observer model extraction method.

    Extracts a Model from state observations using the observer technique.  All
    the fluents present in the observations are saved as is. The actions have
    their preconditions, add effects, and delete effects found and added to the
    object.

    The preconditions of an action are defined as the (positive) intersection
    of all pre-states to that action. The effects are the union off all fluents
    that changed state from a pre-state to a post-state of an action. Add this
    effects are fluents that went from False to True, delete effects are
    fluents that went from True to False.
    """

    def __new__(cls, observations: ObservationList):
        """Creates a new Model object.

        Args:
            observations (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if observations.type is not IdentityObservation:
            raise extract.IncompatibleObservationToken(
                "The Observer extraction technique only works with identity observations. Use `macq.observation.IdentityObservation` as the `Token` when tokenizing traces."
            )
        fluents = Observer._get_fluents(observations)
        actions = Observer._get_actions(observations)
        return Model(fluents, actions)

    @staticmethod
    def _get_fluents(observations: ObservationList):
        """Retrieves the set of fluents in the observations."""
        fluents = set()
        trace: List[Observation]
        for trace in observations:
            for obs in trace:
                # Update fluents with the fluents in this observation
                fluents.update(list(obs.step.state.keys()))
        return fluents

    @staticmethod
    def _get_actions(observations: ObservationList):
        """Retrieves and augments the set of actions in the observations."""
        # Get the unique actions and the relevant traces
        action_obs = defaultdict(list)
        trace_obs: List[Observation]
        for trace_obs in observations:
            for obs in trace_obs:
                action = obs.step.action
                if action is not None:  # Final step has no action
                    action_obs[action].append(trace_obs)

        # Create the ModelActions
        action_pre_states = defaultdict(set)
        for action, obs in action_obs.items():
            model_action = extract.ModelAction(action)
            sas_triples = extract.Extract.get_transitions(action, obs)  # (S,A,S')
            for sas in sas_triples:
                # Add all action pre-states to a set
                action_pre_states[model_action].add(sas.pre_state)
                # Directly add effects
                delta = sas.pre_state.diff_from(sas.post_state)
                model_action.update_add(delta.added)
                model_action.update_delete(delta.deleted)

        for action, pre_states in action_pre_states.items():
            # Find the (positive) intersection of the pre-states
            precond = set.intersection(*map(Observer._filter_positive, pre_states))
            action.update_precond(precond)

        return {action for action in action_pre_states.keys()}

    @staticmethod
    def _filter_positive(state):
        """Returns the set of true fluents in a state."""
        true_fluents = set()
        for fluent, is_true in state.items():
            if is_true:
                true_fluents.add(fluent)
        return true_fluents

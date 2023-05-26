""".. include:: ../../docs/templates/extract/observer.md"""

from collections import defaultdict
from dataclasses import dataclass
from typing import List, Set

from dataclasses import dataclass
from ..observation import IdentityObservation, ObservedTraceList
from . import LearnedAction, Model
from .exceptions import IncompatibleObservationToken
from .learned_fluent import LearnedFluent
from .model import Model


@dataclass
class DeltaObservation:
    added: Set[str]
    deleted: Set[str]


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

    def __new__(cls, obs_tracelist: ObservedTraceList, **kwargs):
        """Creates a new Model object.

        Args:
            observations (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if obs_tracelist.type is not IdentityObservation:
            raise IncompatibleObservationToken(obs_tracelist.type, Observer)
        fluents = Observer._get_fluents(obs_tracelist)
        actions = Observer._get_actions(obs_tracelist)
        return Model(fluents, actions)

    @staticmethod
    def _get_fluents(obs_tracelist: ObservedTraceList):
        """Retrieves the set of fluents in the observations."""
        fluents = set()
        obs_trace: List[IdentityObservation]
        for obs_trace in obs_tracelist:
            for obs in obs_trace:
                # Update fluents with the fluents in this observation
                fluents.update(
                    LearnedFluent(f.name, [o.details() for o in f.objects])
                    for f in obs.state.keys()
                )
        return fluents

    @staticmethod
    def _get_actions(obs_tracelist: ObservedTraceList):
        """Retrieves and augments the set of actions in the observations."""
        # Get the unique actions and the relevant traces
        action_obs = defaultdict(list)
        obs_trace: List[IdentityObservation]
        for obs_trace in obs_tracelist:
            for obs in obs_trace:
                action = obs.action
                if action:  # Final step has no action
                    action_obs[action].append(obs_trace)

        action_pre_states = defaultdict(set)
        # Get transitions for each action
        action_transitions = obs_tracelist.get_all_transitions()
        for action, transitions in action_transitions.items():
            # Create a LearnedAction for the current action
            model_action = LearnedAction(
                action.name, action.obj_params, cost=action.cost
            )

            for pre, post in transitions:
                # Add all action pre-states to a set
                action_pre_states[model_action].add(pre.state)
                # Update the action's effects
                delta = Observer.get_delta(pre.state, post.state)
                model_action.update_add({str(f) for f in delta.added})
                model_action.update_delete({str(f) for f in delta.deleted})

        for action, pre_states in action_pre_states.items():
            # Find the (positive) intersection of the pre-states
            precond = set.intersection(*map(Observer._filter_positive, pre_states))
            action.update_precond({str(f) for f in precond})

        return {action for action in action_pre_states}

    @staticmethod
    def get_delta(pre: dict, post: dict):
        """Determines the delta-state between pre and post.

        Args:
            pre (dict):
                The pre-state to compare.
            post (dict):
                The post-state to compare.

        Returns:
            A `DeltaState` object, containing two sets: `added` and `deleted`.
            The added set contains the list of fluents that were False in this
            state and True in `other`. The deleted set contains the list of
            fluents that were True in this state and False in `other`.
        """
        added = set()
        deleted = set()
        for f in pre:
            if pre[f] and not post[f]:  # true pre, false post -> deleted
                deleted.add(f)
            elif not pre[f] and post[f]:  # false pre, true post -> added
                added.add(f)
        return DeltaObservation(added, deleted)

    @staticmethod
    def _filter_positive(state):
        """Returns the set of true fluents in a state."""
        true_fluents = set()
        for fluent, is_true in state.items():
            if is_true:
                true_fluents.add(fluent)
        return true_fluents

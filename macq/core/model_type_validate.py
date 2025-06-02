from enum import Enum
from typing import Set, TypeVar

from macq.core import LiftedAction, GroundedAction, LiftedFluent, GroundedFluent

LiftedFeature = LiftedFluent | LiftedAction
GroundedFeature = GroundedFluent | GroundedAction

class ModelType(Enum):
    """Enumeration of supported model types."""
    LIFTED = "lifted"
    GROUNDED = "grounded"
    MIXED = "mixed"  # For cases where you might have both
    UNKNOWN = "unknown"

#todo: make informative
class ModelValidationError(Exception):
    """Raised when model components are inconsistent."""
    pass



class ModelTypeValidator:
    """Utility class for validating model type consistency."""

    @staticmethod
    def detect_feature_type(feature_set: Set) -> ModelType:
        """Detect the type of in a set."""
        if not feature_set:
            return ModelType.UNKNOWN

        first_item = next(iter(feature_set))

        if isinstance(first_item, LiftedFeature):
            # Check if all actions are lifted
            if all(isinstance(feature_item, LiftedFeature) for feature_item in feature_set):
                return ModelType.LIFTED
            else:
                return ModelType.MIXED

        elif isinstance(first_item, GroundedFeature):
            # Check if all actions are grounded
            if all(isinstance(feature_item, GroundedFeature) for feature_item, in feature_set):
                return ModelType.GROUNDED
            else:
                return ModelType.MIXED
        else:
            return ModelType.UNKNOWN


    @staticmethod
    def validate_model_consistency(actions: Set, fluents: Set) -> ModelType:
        """Validate that actions and fluents are consistent with each other."""
        action_type = ModelTypeValidator.detect_feature_type(actions)
        fluent_type = ModelTypeValidator.detect_feature_type(fluents)

        if action_type == ModelType.UNKNOWN or fluent_type == ModelType.UNKNOWN:
            return ModelType.UNKNOWN
        else:
            if action_type == fluent_type:
                return action_type
            else:
                raise ModelValidationError(
                    f"Inconsistent model types: actions are {action_type.value} "
                    f"but fluents are {fluent_type.value}"
                )


    #replaced with detect_feature_type for less code.
    # @staticmethod
    # def detect_action_type(actions: Set) -> ModelType:
    #     """Detect the type of actions in a set."""
    #     if not actions:
    #         return ModelType.UNKNOWN
    #
    #     first_action = next(iter(actions))
    #
    #     if isinstance(first_action, LiftedAction):
    #         # Check if all actions are lifted
    #         if all(isinstance(action, LiftedAction) for action in actions):
    #             return ModelType.LIFTED
    #         else:
    #             return ModelType.MIXED
    #     elif isinstance(first_action, GroundedAction):
    #         # Check if all actions are grounded
    #         if all(isinstance(action, GroundedAction) for action in actions):
    #             return ModelType.GROUNDED
    #         else:
    #             return ModelType.MIXED
    #     else:
    #         return ModelType.UNKNOWN
    #
    # @staticmethod
    # def detect_fluent_type(fluents: Set) -> ModelType:
    #     """Detect the type of fluents in a set."""
    #     if not fluents:
    #         return ModelType.UNKNOWN
    #
    #     first_fluent = next(iter(fluents))
    #
    #     if isinstance(first_fluent, LiftedFluent):
    #         # Both LiftedFluent and ParameterBoundLiteral work with lifted models
    #         if all(isinstance(fluent, LiftedFluent) for fluent in fluents):
    #             return ModelType.LIFTED
    #         else:
    #             return ModelType.MIXED
    #     elif isinstance(first_fluent, GroundedFluent):
    #         if all(isinstance(fluent, GroundedFluent) for fluent in fluents):
    #             return ModelType.GROUNDED
    #         else:
    #             return ModelType.MIXED
    #     else:
    #         return ModelType.UNKNOWN
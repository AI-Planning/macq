from typing import Set, Union, List, Optional

from .action_model import Model
from .actions import GroundedAction, LiftedAction
from .fluents import LiftedFluent, ParameterBoundFluent, GroundedFluent
from .model_type_validate import ModelTypeValidator, ModelType, ModelValidationError


# Factory Functions - The main interface for creating models

def create_lifted_model(
    fluents: Set[Union[LiftedFluent, ParameterBoundFluent]],
    actions: Set[LiftedAction],
    learned_sorts: Optional[List] = None
) -> Model:
    """
    Create a lifted model with type validation.
    
    Args:
        fluents: Set of LiftedFluent or ParameterBoundLiteral objects
        actions: Set of LiftedAction objects
        learned_sorts: Optional list of sorts
    
    Returns:
        A validated lifted Model
    
    Raises:
        ModelValidationError: If the provided components are not consistent
    """
    # Validate types
    for fluent in fluents:
        if not isinstance(fluent, (LiftedFluent, ParameterBoundFluent)):
            raise ModelValidationError(
                f"Expected LiftedFluent or ParameterBoundLiteral, got {type(fluent)}"
            )
    
    for action in actions:
        if not isinstance(action, LiftedAction):
            raise ModelValidationError(
                f"Expected LiftedAction, got {type(action)}"
            )
    
    return Model(
        fluents=fluents, 
        actions=actions, 
        learned_sorts=learned_sorts,
        model_type=ModelType.LIFTED,
        _skip_validation=True  # We already validated
    )

def create_grounded_model(
    fluents: Set[GroundedFluent], 
    actions: Set[GroundedAction],
    learned_sorts: Optional[List] = None
) -> Model:
    """
    Create a grounded model with type validation.
    
    Args:
        fluents: Set of GroundedFluent objects
        actions: Set of GroundedAction objects
        learned_sorts: Optional list of sorts
    
    Returns:
        A validated grounded Model
    
    Raises:
        ModelValidationError: If the provided components are not consistent
    """
    # Validate types
    for fluent in fluents:
        if not isinstance(fluent, GroundedFluent):
            raise ModelValidationError(
                f"Expected GroundedFluent, got {type(fluent)}"
            )
    
    for action in actions:
        if not isinstance(action, GroundedAction):
            raise ModelValidationError(
                f"Expected GroundedAction, got {type(action)}"
            )
    
    return Model(
        fluents=fluents, 
        actions=actions, 
        learned_sorts=learned_sorts,
        model_type=ModelType.GROUNDED,
        _skip_validation=True  # We already validated
    )

def create_model_from_components(
    fluents: Set,
    actions: Set,
    learned_sorts: Optional[List] = None
) -> Model:
    """
    Create a model by auto-detecting the type from components.

    Args:
        fluents: Set of fluent objects
        actions: Set of action objects
        learned_sorts: Optional list of sorts

    Returns:
        A validated Model of the appropriate type

    Raises:
        ModelValidationError: If the components are inconsistent or unknown type
    """
    model_type = ModelTypeValidator.validate_model_consistency(actions, fluents)

    if model_type == ModelType.UNKNOWN:
        raise ModelValidationError("Cannot determine model type from provided components")

    return Model(
        fluents=fluents,
        actions=actions,
        learned_sorts=learned_sorts,
        model_type=model_type,
        _skip_validation=True)


# Usage examples and type-safe functions

def merge_models_safe(model1: Model, model2: Model) -> Model:
    """Safely merge two models of the same type."""
    if model1.model_type != model2.model_type:
        raise ModelValidationError(
            f"Cannot merge models of different types: {model1.model_type.value} "
            f"and {model2.model_type.value}"
        )
    
    merged_fluents = model1.fluents | model2.fluents
    merged_actions = model1.actions | model2.actions
    
    # Merge learned_sorts
    merged_sorts = None
    if model1.learned_sorts and model2.learned_sorts:
        merged_sorts = list(set(model1.learned_sorts + model2.learned_sorts))
    elif model1.learned_sorts:
        merged_sorts = model1.learned_sorts
    elif model2.learned_sorts:
        merged_sorts = model2.learned_sorts
    
    return create_model_from_components(merged_fluents, merged_actions, merged_sorts)

# def convert_to_grounded(lifted_model: Model, objects: List) -> Model:
#     """Convert a lifted model to a grounded model (placeholder implementation)."""
    # if not lifted_model.is_lifted_model():
    #     raise ModelValidationError("Can only ground lifted models")
    #
    # # This would contain your actual grounding logic
    # # For now, it's just a placeholder
    # grounded_fluents = set()  # Your grounding logic here
    # grounded_actions = set()   # Your grounding logic here
    #
    # return create_grounded_model(grounded_fluents, grounded_actions)
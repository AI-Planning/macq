import pytest

from macq.extract.learned_action import LearnedLiftedAction, LiftedActionNegPrec
from macq.extract.learned_fluent import LearnedLiftedFluent, ParamBoundLFluent
from macq.extract.learned_sort import Sort
from macq.extract.model import Model


def test_negative_precondition_actions_with_different_names_are_distinct():
    actions = {LiftedActionNegPrec("pick", ["t"]), LiftedActionNegPrec("drop", ["t"])}

    assert len(actions) == 2


def test_negative_precondition_action_stays_in_a_set_after_being_updated():
    action = LiftedActionNegPrec("pick", ["t"])
    actions = {action}

    action.update_precond(ParamBoundLFluent("clear", ["t"], [0]))

    assert action in actions


def export_domain(model, tmp_path):
    """Exports the model and returns the domain text with whitespace collapsed."""
    domain_file = tmp_path / "domain.pddl"
    model.to_pddl(
        "test",
        domain_filename=str(domain_file),
        problem_filename=str(tmp_path / "problem.pddl"),
    )
    return " ".join(domain_file.read_text().split())


def test_predicate_used_with_different_argument_orders_is_declared_once(tmp_path):
    on_ab = ParamBoundLFluent("on", ["t", "t"], [0, 1])
    on_ba = ParamBoundLFluent("on", ["t", "t"], [1, 0])
    swap = LearnedLiftedAction(
        "swap", ["t", "t"], precond={on_ab}, add={on_ba}, delete={on_ab}
    )

    domain = export_domain(Model({on_ab, on_ba}, {swap}), tmp_path)

    assert domain.count("(on ?x1 - t ?x2 - t)") == 1
    assert ":precondition (on ?x0 ?x1)" in domain
    assert "(on ?x1 ?x0) (not (on ?x0 ?x1))" in domain


def test_predicate_declared_with_conflicting_types_is_rejected(tmp_path):
    at_truck = ParamBoundLFluent("at", ["truck"], [0])
    at_plane = ParamBoundLFluent("at", ["plane"], [0])
    go = LearnedLiftedAction("go", ["truck"], precond={at_truck})

    with pytest.raises(ValueError, match="at"):
        export_domain(Model({at_truck, at_plane}, {go}), tmp_path)


def hierarchy_model(sorts):
    at = ParamBoundLFluent("at", ["vehicle"], [0])
    go = LearnedLiftedAction("go", ["truck"], precond={at}, add={at})
    return Model({at}, {go}, learned_sorts=sorts)


def test_type_hierarchy_is_exported(tmp_path):
    sorts = [Sort("thing"), Sort("vehicle", "thing"), Sort("truck", "vehicle")]

    domain = export_domain(hierarchy_model(sorts), tmp_path)

    assert "thing - object" in domain
    assert "vehicle - thing" in domain
    assert "truck - vehicle" in domain


def test_child_type_may_be_listed_before_its_parent(tmp_path):
    sorts = [Sort("truck", "vehicle"), Sort("vehicle", "thing"), Sort("thing")]

    domain = export_domain(hierarchy_model(sorts), tmp_path)

    assert "vehicle - thing" in domain
    assert "truck - vehicle" in domain


def test_type_with_unknown_parent_is_rejected(tmp_path):
    sorts = [Sort("vehicle"), Sort("truck", "missing")]

    with pytest.raises(ValueError, match="missing"):
        export_domain(hierarchy_model(sorts), tmp_path)


def test_cyclic_type_hierarchy_is_rejected(tmp_path):
    sorts = [Sort("vehicle", "truck"), Sort("truck", "vehicle")]

    with pytest.raises(ValueError, match="[Cc]ycl"):
        export_domain(hierarchy_model(sorts), tmp_path)


def test_negative_preconditions_are_exported(tmp_path):
    holding = ParamBoundLFluent("holding", ["t"], [0])
    clear = ParamBoundLFluent("clear", ["t"], [0])
    pick = LiftedActionNegPrec(
        "pick", ["t"], precond={clear}, negative_precond={holding}, add={holding}
    )

    domain = export_domain(Model({holding, clear}, {pick}), tmp_path)

    assert ":precondition (and (clear ?x0) (not (holding ?x0)))" in domain


def test_only_a_negative_precondition_is_exported(tmp_path):
    holding = ParamBoundLFluent("holding", ["t"], [0])
    pick = LiftedActionNegPrec(
        "pick", ["t"], negative_precond={holding}, add={holding}
    )

    domain = export_domain(Model({holding}, {pick}), tmp_path)

    assert ":precondition (not (holding ?x0))" in domain


def test_model_details_list_negative_preconditions():
    holding = ParamBoundLFluent("holding", ["t"], [0])
    pick = LiftedActionNegPrec("pick", ["t"], negative_precond={holding})

    details = Model({holding}, {pick}).details()

    assert "negative precond:" in details
    assert "(holding t ) [0]" in details.split("negative precond:")[1]


def test_models_with_different_learned_types_are_not_equal():
    fluent = LearnedLiftedFluent("p", ["t"], [0])

    assert Model({fluent}, set(), [Sort("t")]) != Model({fluent}, set(), [Sort("x")])


def test_learned_type_order_does_not_affect_model_equality():
    fluent = LearnedLiftedFluent("p", ["t"], [0])
    sorts = [Sort("t"), Sort("x", "t")]

    assert Model({fluent}, set(), sorts) == Model({fluent}, set(), sorts[::-1])


def test_param_bound_fluents_are_distinguished_by_argument_order():
    assert ParamBoundLFluent("on", ["t", "t"], [0, 1]) != ParamBoundLFluent(
        "on", ["t", "t"], [1, 0]
    )


def test_param_bound_fluent_converts_to_a_lifted_fluent():
    lifted = ParamBoundLFluent("on", ["a", "b"], [1, 0]).to_LearnedLiftedFluent()

    assert isinstance(lifted, LearnedLiftedFluent)
    assert (lifted.name, lifted.param_sorts, lifted.param_act_inds) == (
        "on",
        ["a", "b"],
        [1, 0],
    )

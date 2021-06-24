import macq.extract as extract
from typing import Union, List, Set
from nnf import Var, Or, And, true, false
from ..observation import Observation, PartialObservabilityToken
from ..trace import Action, ObservationList


class Slaf:
    # only need one true and one false
    top = true
    bottom = false

    def __new__(cls, observations: ObservationList):
        """Creates a new Model object.

        Args:
            observations (ObservationList):
                The state observations to extract the model from.
        Raises:
            IncompatibleObservationToken:
                Raised if the observations are not identity observation.
        """
        if observations.type is not PartialObservabilityToken:
            raise extract.IncompatibleObservationToken(observations.type, Slaf)
        Slaf.as_strips_slaf(observations)

    @staticmethod
    def __get_initial_fluent_factored(
        observation: Observation, raw_fluent_factored: Union[List, None]
    ):
        """Gets the initial fluent-factored formula of an observation/trace.

        Args:
            observation (Observation):
                The observation to extract the fluent-factored formula from.

        Returns:
            A list of dictionaries that holds the fluent-factored formula.
        """
        top = Slaf.top
        bottom = Slaf.bottom
        if not raw_fluent_factored:
            raw_fluent_factored = []
        fluents = set()

        all_fluents = [f for token in observation for f in token.get_all_base_fluents()]
        for f in all_fluents:
            fluents.add(f)

        # get previous fluents
        old_fluents = set()
        for f in raw_fluent_factored:
            old_fluents.add(f["fluent"].details)

        # set up the initial fluent factored form for the problem
        for f in fluents:
            if f not in old_fluents:
                phi = {}
                phi["fluent"] = Var(f)
                phi["pos expl"] = top
                phi["neg expl"] = top
                phi["neutral"] = top
                raw_fluent_factored.append(phi)
        return raw_fluent_factored

    @staticmethod
    def as_strips_slaf(observations: ObservationList, debug: bool = False):
        """Implements the AS-STRIPS-SLAF algorithm from section 5.3 of the SLAF paper.
        Iterates through the action/observation pairs of each observation/trace, returning
        a fluent-factored transition belief formula that filters according to that action/observation.
        The transition belif formulas for each trace/observation are conjoined to get one final formula,
        which is then solved using a SAT solver to extract models.

        Args:
            observations (ObservationList):
                The list of observations/traces to apply the filtering algorithm to.
        """
        # get global variables
        top = Slaf.top
        bottom = Slaf.bottom
        validity_constraints = set()

        raw_fluent_factored = None
        # iterate through every observation in the list of observations/traces
        for obs in observations:
            # get the fluent factored formula for this observation/trace
            raw_fluent_factored = Slaf.__get_initial_fluent_factored(
                obs, raw_fluent_factored
            )
            if debug:
                all_f_details = [f["fluent"].name for f in raw_fluent_factored]
                all_f_details.sort()
                for f in all_f_details:
                    print(f)
                to_obs = []
                user_input = ""
                while user_input != "x":
                    user_input = input(
                        "Which fluents do you want to observe? Enter 'x' when you are finished.\n"
                    )
                    if user_input in all_f_details:
                        to_obs.append(user_input)
                        print(user_input + " added to the debugging list.")
                    else:
                        if user_input != "x":
                            print("The fluent you entered is invalid.")

            # iterate through all tokens (action/observation pairs) in this observation/trace
            for token in obs:
                # steps 1. (d)-(e) of AS-STRIPS-SLAF
                # NEED TO CHECK THE VALUE OF THE FLUENT HERE
                all_o = [
                    Var(f.details()) if token.step.state[f] else ~Var(f.details())
                    for f in token.step.state.fluents
                ]
                for phi in raw_fluent_factored:
                    f = phi["fluent"]

                    for o in all_o:
                        # "negated" fluents are of type CustomNNF, and all f are of type Var
                        if f == o:
                            phi["pos expl"] = top
                            phi["neg expl"] = bottom
                            phi["neutral"] = (
                                (phi["neutral"] & phi["pos expl"]).simplify().to_CNF()
                            )
                        if ~f == o:
                            phi["pos expl"] = bottom
                            phi["neg expl"] = top
                            phi["neutral"] = (
                                (phi["neutral"] & phi["neg expl"]).simplify().to_CNF()
                            )

                # iterate through every fluent in the fluent-factored transition belief formula
                # steps 1. (a)-(c) of AS-STRIPS-SLAF, page 366
                # "if a" ensures that the action is not None (happens on the last step of a trace)
                a = token.step.action
                if a:
                    for phi in raw_fluent_factored:
                        f = phi["fluent"]

                        pos_precond = Var(f"{f} is a precondition of {a.details()}")
                        neg_precond = Var(f"(~{f} is a precondition of {a.details()})")
                        pos_effect = Var(f"{a.details()} causes {f}")
                        neg_effect = Var(f"{a.details()} causes ~{f}")
                        neutral = Var(f"{a.details()} has no effect on {f}")

                        phi["neutral"] = (
                            (
                                (~pos_precond | phi["pos expl"])
                                & (~neg_precond | phi["neg expl"])
                                & phi["neutral"]
                            )
                            .simplify()
                            .to_CNF()
                        )
                        phi["pos expl"] = (
                            pos_effect
                            | (neutral & ~neg_precond & phi["pos expl"])
                            .simplify()
                            .to_CNF()
                        )

                        phi["neg expl"] = (
                            neg_effect
                            | (neutral & ~pos_precond & phi["neg expl"])
                            .simplify()
                            .to_CNF()
                        )

                        validity_constraints.add(pos_effect | neg_effect | neutral)
                        validity_constraints.add(
                            (~pos_effect | ~neg_effect)
                            & (~neg_effect | ~neutral)
                            & (~pos_effect | ~neutral)
                        )
                        validity_constraints.add(~pos_precond | ~neg_precond)
                if debug:
                    print("-" * 100)
                    if a:
                        print("\nAction taken: " + a.details() + "\n")
                    for obj in to_obs:
                        for phi in raw_fluent_factored:
                            f_str = phi["fluent"].name
                            if f_str == obj:
                                print("\nfluent: " + f_str)
                                print("\nexpl. for fluent being true:")
                                print(phi["pos expl"])
                                print("\nexpl. for fluent being false:")
                                print(phi["neg expl"])
                                print("\nexpl. for fluent being unaffected:")
                                print(phi["neutral"])
                    print()
                    user_input = input("Hit enter to continue.")

        formula = []
        # convert to formula once you have stepped through the whole observation/trace and applied all transformations
        # add as constraints to e here
        for phi in raw_fluent_factored:
            f = phi["fluent"]
            # convert to formula for each fluent
            formula.append(~f | phi["pos expl"])
            formula.append(f | phi["neg expl"])
            formula.append(phi["neutral"])
        formula.extend(validity_constraints)
        full_formula = And({*[f for f in formula]})
        solution = full_formula.solve()

        f = open("output.txt", "w")
        keys = list(solution.keys())
        keys = [str(f) for f in keys]
        keys.sort()
        for key in keys:
            try:
                f.write(str(key) + ": " + str(solution[key]) + "\n")
            except:
                f.write("aux\n")
        f.close()

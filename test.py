from pathlib import Path
from collections import Counter
from macq.extract import Extract, modes
from macq.observation import IdentityObservation, Observation
from macq.trace import *
from macq import generate, extract
from macq.generate.pddl import VanillaSampling, TraceFromGoal


def generate_traces():
    # traces = generate.pddl.VanillaSampling(
    #     problem_id=2336, plan_len=5, num_traces=3, seed=42
    # ).traces
    # traces.generate_more(1)
    base = Path(__file__).parent
    dom = (base / "tests/pddl_testing_files/blocks_domain.pddl").resolve()
    prob = (base / "tests/pddl_testing_files/blocks_problem.pddl").resolve()
    traces = VanillaSampling(dom=dom, prob=prob, plan_len=5, num_traces=1).traces  # type: ignore

    return traces


def extract_model(traces):
    observations = traces.tokenize(IdentityObservation)
    model = extract.Extract(observations, extract.modes.OBSERVER)
    return model


def _pysat():
    from pysat.examples.rc2 import RC2
    from pysat.formula import WCNF
    from nnf import And, Or, Var

    vars = [Var(f"var{n}") for n in range(1, 4)]
    sentence = And([Or([vars[0], vars[1]]), Or([vars[0], vars[2].negate()])])

    decode = dict(enumerate(sentence.vars(), start=1))
    encode = {v: k for k, v in decode.items()}
    clauses = [
        [encode[var.name] if var.true else -encode[var.name] for var in clause]
        for clause in sentence
    ]
    print("decode:", decode)
    print("encode:", encode)
    print("clauses:", clauses)

    wcnf = WCNF()
    wcnf.extend(clauses, weights=[1, 2])
    print("wcnf:", wcnf)
    solver = RC2(wcnf)
    solver.compute()
    print("cost:", solver.cost)
    print("model:", solver.model)
    print("decoded model:")
    for clause in solver.model:  # type: ignore
        print("  ", decode[abs(clause)], end="")
        if clause > 0:
            print(" - true")
        else:
            print(" - false")
    print("\nenumerating all models ...")
    print("model      cost")
    for model in solver.enumerate():
        print(model, solver.cost)


def apriori():
    minsup = 2
    action_lists = [
        ["a", "b", "c", "d"],
        ["a", "c", "b", "c"],
        ["b", "c", "a", "d"],
    ]
    counts = Counter([action for action_list in action_lists for action in action_list])
    # L1 = {actions that appear >minsup}
    L1 = set(
        frozenset(action)
        for action in filter(lambda k: counts[k] >= minsup, counts.keys())
    )  # large 1-itemsets

    # Only going up to L2, so no loop or generalized algorithm needed
    # apriori-gen step
    C2 = set([i.union(j) for i in L1 for j in L1 if len(i.union(j)) == 2])
    C2_ordered = set()
    for pair in C2:
        pair = list(pair)
        C2_ordered.add((pair[0], pair[1]))
        C2_ordered.add((pair[1], pair[0]))

    L2 = set()
    for a1, a2 in C2_ordered:
        count = 0
        print(f"({a1}, {a2})")
        for action_list in action_lists:
            print(f"action_list: {action_list}")
            a1_indecies = [i for i, e in enumerate(action_list) if e == a1]
            print(f"a1_indecies: {a1_indecies}")
            if a1_indecies:
                for i in a1_indecies:
                    print("after", i)
                    if a2 in action_list[i + 1 :]:
                        print("+1")
                        count += 1
        if count >= minsup:
            print("added")
            L2.add((a1, a2))
        print()
    print(L2)
    # Since L1 contains 1-itemsets where each item is frequent, C2 can
    # only contain valid sets and pruning is not required


"""
def generate_traces():
    # traces = generate.pddl.VanillaSampling(
    #     problem_id=2336, plan_len=5, num_traces=3, seed=42
    # ).traces
    # traces.generate_more(1)
    base = Path(__file__).parent
    dom = (base / "tests/pddl_testing_files/blocks_domain.pddl").resolve()
    prob = (base / "tests/pddl_testing_files/blocks_problem.pddl").resolve()
    traces = VanillaSampling(dom=dom, prob=prob, plan_len=100, num_traces=1).traces  # type: ignore

    return traces


def extract_model(traces):
    observations = traces.tokenize(IdentityObservation)
    model = extract.Extract(observations, extract.modes.OBSERVER)
    return model
"""


def get_fluent(name: str, objs: list[str]):
    objects = [PlanningObject(o.split()[0], o.split()[1]) for o in objs]
    return Fluent(name, objects)


def arms():
    base = Path(__file__).parent
    dom = str((base / "tests/pddl_testing_files/blocks_domain.pddl").resolve())
    prob = str((base / "tests/pddl_testing_files/blocks_problem.pddl").resolve())

    traces = TraceList()
    generator = TraceFromGoal(dom=dom, prob=prob)
    # for f in generator.trace.fluents:
    #     print(f)

    generator.change_goal(
        {
            get_fluent("on", ["object a", "object b"]),
            get_fluent("on", ["object b", "object c"]),
        }
    )
    traces.append(generator.generate_trace())
    generator.change_goal(
        {
            get_fluent("on", ["object b", "object a"]),
            get_fluent("on", ["object c", "object b"]),
        }
    )
    traces.append(generator.generate_trace())
    traces.print("color")


if __name__ == "__main__":
    # apriori()
    # _pysat()
    # traces = generate_traces()
    # model = extract_model(traces)
    # actions = list(model.actions)
    # pre = list(actions[0].precond)
    # print(type(pre[0]))
    arms()

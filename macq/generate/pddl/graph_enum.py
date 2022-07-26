from tarski.search.operations import progress
import networkx as nx
import random
import macq
from macq.generate.pddl import Generator
from macq.utils import (
    set_timer_throw_exc,
    TraceSearchTimeOut,
    InvalidTime,
    set_num_traces,
    set_plan_length,
    progress as print_progress,
)
from macq.trace import (
    Step,
    Trace,
    TraceList,
)


class Graph_enum(Generator):
    

    def __init__(
        self,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
        observe_pres_effs: bool = False,
        plan_len: int = 1,
        num_traces: int = 0,
        seed: int = None,
        max_time: float = 30,
    ):
        super().__init__(
            dom=dom,
            prob=prob,
            problem_id=problem_id,
            observe_pres_effs=observe_pres_effs,
        )

        if self.num_traces > 0:
            self.traces = self.generate_traces()
        else:
            self.traces = None
        if seed:
            random.seed(seed)

        DG=nx.DiGraph()

    def generate_traces(self):
        """Generates traces randomly by uniformly sampling applicable actions to find plans
        of the given length.

        Returns:
            A TraceList object with the list of traces generated.
        """
        traces = TraceList()
        traces.generator = self.generate_single_trace_setup(
            num_seconds=self.max_time, plan_len=self.plan_len
        )
        for _ in print_progress(range(self.num_traces)):
            traces.append(traces.generator())
        self.traces = traces
        return traces

    def generate_single_trace_setup(self, num_seconds: float, plan_len = None):
        @set_timer_throw_exc(
            num_seconds=num_seconds, exception=TraceSearchTimeOut, max_time=num_seconds
        )
        def generate_single_trace(self=self, plan_len=plan_len):
            """Generates a single trace using the uniform random sampling technique.
            Loops until a valid trace is found. The timer wrapper does not allow the function
            to run past the time specified.

            The outside function is a wrapper that provides parameters for both the timer
            wrapper and the function.

            Returns:
                A Trace object (the valid trace generated).
            """

            if not plan_len:
                plan_len = self.plan_len
            if callable(plan_len):
                plan_len = plan_len()

            trace = Trace()
            

            state = self.problem.init
            DG.add_node(state)
            Visited={node:False for node in G.nodes}

            Queue= [state]
            Visited[state]=True
            while Queue:
                cur_node = Queue.pop(0)
                Result.append(cur_node)
                app_act = list(self.instance.applicable(cur_node))
                for act in app_act:
                    next_state = progress(cur_node, act)
                    if next_state not in list(G.nodes): 
                        G.add_node(next_state)
                        Visited[next_state]=False
                    G.add_edge(cur_node,next_state, action= act)
                for node in G.neighbors(cur_node):
                    if (Visited[node]==False):
                            Queue.append(node)
                            Visited[node]=True
            
'''print(Result)
nx.draw(G, with_labels=True)
plt.draw
plt.show



            Visited={node:False for node in G.nodes}
            Queue[state]
            Visited[state]=True
            while Queue:
                cur_node = Queue.pop(0)
                app_act = list(self.instance.applicable(cur_node))

                Result.append(cur_node)
                for node in G.neighbors(cur_node):
                    if not Visited[node]:
                        Queue.append(node)
                        Visited[node]=True
                print("Result:","->".join(Result))
            app_act = list(self.instance.applicable(state))
            for i in app_act:
                next_state=progress(state, i)
                            if next_state in digraph:
                                add edge(next_state, old_state , action=i)
                            
                            else:
                                add_edge(state, next_state, action=i)
'''




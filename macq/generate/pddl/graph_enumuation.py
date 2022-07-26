import matplotlib.pyplot as plt
from tarski.search.operations import progress
import networkx as nx
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
        num_traces: int = 1,
        
    ):
        super().__init__(
            dom=dom,
            prob=prob,
            problem_id=problem_id,
            observe_pres_effs=observe_pres_effs,
        )
        
        
        
        self.num_traces = set_num_traces(num_traces)
        if self.num_traces > 0:
            self.traces = self.generate_graph()
        else:
            self.traces = None
        #self.traces = self.generate_graph()
        

       
    def generate_graph(self):
        G=nx.DiGraph()
        state = self.problem.init
        G.add_node(state)
        Visited={node:False for node in G.nodes}

        Queue= [state]
        Visited[state]=True
        while Queue:
            cur_node = Queue.pop(0)
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
        return G
            

DG= Graph_enum(prob='C:/Users/User/tarski/docs/notebooks/benchmarks/probBLOCKS-4-2.pddl', dom='C:/Users/User/tarski/docs/notebooks/benchmarks/blocksworld.pddl',num_traces=1).traces
plt.figure(figsize=(50,50))
pos = nx.spring_layout(DG)
nx.draw(DG,pos)

edge_labels = dict([((n1, n2), d['action'])
                    for n1, n2, d in DG.edges(data=True)])

nx.draw_networkx_edge_labels(DG,pos,edge_labels=edge_labels,font_size=5, font_weight='bold')

plt.show()
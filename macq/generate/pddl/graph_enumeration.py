import matplotlib.pyplot as plt
from tarski.search.operations import progress
import networkx as nx
import macq
import pygraphviz
from macq.generate.pddl import Generator
import math
from macq.trace import (
    State,
    Trace,
    Action,
)

class Step:
    
    def __init__(self, state: State, action: Action, next_state: State, index: int):
        
        self.state = state
        self.action = action
        self.index = index
        self.next_state=next_state


class Graph_enum(Generator):
    
    def __init__(
        self,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
        num_nodes: int = math.inf,
        
    ):
        super().__init__(
            dom=dom,
            prob=prob,
            problem_id=problem_id,
        )

        self.num_nodes = num_nodes
        if num_nodes > 0:
            self.traces = self.generate_traces()
        else:
            self.traces = None



    def generate_traces(self):
        traces = self.generate_single_trace()
        self.traces=traces
        return traces

        
        
        #self.traces = self.generate_graph()
        
    def generate_single_trace(self):
        
        trace = Trace()
        graph= self.generate_graph()

        edge_labels = dict([((n1, n2), d['label'])
                    for n1, n2, d in graph.edges(data=True)])

        DFS=list(nx.edge_dfs(graph,list(graph.nodes)[0]))
        count=1
        for i in DFS:
            macq_action = self.tarski_act_to_macq(edge_labels.get(i))
            macq_cur_state = self.tarski_state_to_macq(i[0])
            macq_next_state = self.tarski_state_to_macq(i[1])
            step = Step(macq_cur_state, macq_action,macq_next_state, count)
            count+=1
            trace.append(step)
            
        return trace


       
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
                if next_state not in Visited: 
                    if self.num_nodes>1:
                        #print(x)
                        G.add_node(next_state)
                        Visited[next_state]=False
                        self.num_nodes-= 1
                    else:
                        return G
                G.add_edge(cur_node,next_state, label= act)
            for node in G.neighbors(cur_node):
                if (Visited[node]==False):
                    Queue.append(node)
                    Visited[node]=True
        return G
            

DG= Graph_enum(prob='C:/Users/User/tarski/docs/notebooks/benchmarks/probBLOCKS-4-2.pddl', dom='C:/Users/User/tarski/docs/notebooks/benchmarks/blocksworld.pddl').traces
print(DG)
'''plt.figure(figsize=(50,50))
pos = nx.spring_layout(DG)
nx.draw(DG,pos)

edge_labels = dict([((n1, n2), d['label'])
                    for n1, n2, d in DG.edges(data=True)])

nx.draw_networkx_edge_labels(DG,pos,edge_labels=edge_labels,font_size=5)
plt.show()

A = nx.nx_agraph.to_agraph(DG)
A.write("k1.dot")  # write to dot file
X3 = nx.nx_agraph.read_dot("k1.dot")  # read from dotfile

#A.draw("k1.png", prog="neato")
'''
from tarski.search.operations import progress
import networkx as nx
from macq.generate.pddl import Generator
import math
from macq.trace import (
    State,
    Trace,
    Action,
    TraceList,
    Step,
)


class StateEnumerator(Generator):
    
    """State Enumerator - inherits the base Generator class and its attributes.

    A trace generator that generates traces of length 2 from a graph where nodes are the states and the edges represent the applicable actions

    Attributes:
        num_nodes (int):
            The number of nodes to be generated in the state space.
        traces (TraceList):
            The list of traces generated.
        dom (str):
            Describes the problem domain
        prob (str):
            Describes the problem
            """
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
        """Generates n traces of length 2 using the graph generated 
        where n= num_nodes or for all the possible states if num_nodes is not defined

        Returns:
            A TraceList object with the list of traces generated.
        """
        traces = TraceList()
        
        graph= self.generate_graph()

        #act is a dictionary with key='label' of the form {'label': action}       
        for cur_state, next_state, act in graph.edges(data=True):
            trace = Trace()
            
            macq_action = self.tarski_act_to_macq(act['label'])
            macq_cur_state = self.tarski_state_to_macq(cur_state)
            macq_next_state = self.tarski_state_to_macq(next_state)
            step = Step(macq_cur_state, macq_action,1)
            trace.append(step)

            step = Step(state=macq_next_state, action=None, index=2)
            trace.append(step)
            traces.append(trace)
        
        self.traces = traces
        return traces
     
    def generate_graph(self):
        """Generates a networkx strictly directed graph for the given problem by expanding the tree using bfs.
        
        Queue[]= Keeps track of all the nodes to be explored
        Visited{node: Bool}= Keeps track of the explored nodes

        Returns:
            A networkx graph with nodes representing states and edges describing the reachable states and action.
        
        """
        G=nx.DiGraph()
        state = self.problem.init #initial state/ root node
        G.add_node(state)
        Visited={ }
        Queue= [state]

        Visited[state]=True
        while Queue:
            cur_node = Queue.pop(0)
            app_act = list(self.instance.applicable(cur_node))
            for act in app_act:

                #creating new node if it doesn't exist in Visited as all the nodes are added to Visited with bool T/F
                next_state = progress(cur_node, act)
                if next_state not in Visited: 
                    if self.num_nodes>1:
                        G.add_node(next_state)
                        Visited[next_state]=False
                        self.num_nodes-= 1
                    else:
                        return G
                G.add_edge(cur_node,next_state, label= act)
            
            #adding node to queue if it hasn't been explored
            for node in G.neighbors(cur_node):
                if (Visited[node]==False):
                    Queue.append(node)
                    Visited[node]=True
        return G
            


import networkx as nx
#import tarski as tr 
import macq
from tarski.io import PDDLReader
import requests


class Generator:


    def __init__(
        self,
        dom: str = None,
        prob: str = None,
        problem_id: int = None,
        observe_pres_effs: bool = False,
    ):

        # get attributes
        self.pddl_dom = dom
        self.pddl_prob = prob
        self.problem_id = problem_id
        self.observe_pres_effs = observe_pres_effs
        # read the domain and problem
        reader = PDDLReader(raise_on_error=True)
        if not problem_id:
            reader.parse_domain(dom)
            self.problem = reader.parse_instance(prob)
        else:
            dom = requests.get(get_problem(problem_id)["domain_url"]).text
            prob = requests.get(get_problem(problem_id)["problem_url"]).text
            reader.parse_domain_string(dom)
            self.problem = reader.parse_instance_string(prob)
        self.lang = self.problem.language

#x= Generator(problem_id=9348)

DG = nx.DiGraph()
for i in x.problem:
    DG.add_edge(x.curr_state, x.next_state,{"action": x.action}) 

opened= []
closed= []

bfs=nx.bfs_edges(DG)
for i in bfs:

    if i not in closed():
        opened.append(i)
        DG.add_edge(x.curr_state, x.next_state,{"action": x.action})




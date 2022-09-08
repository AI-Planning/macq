from typing import Hashable
from macq.extract import Model
from bauhaus import Encoding, constraint, proposition
from dataclasses import dataclass
from macq.observation import ObservationLists

class BGLearner:

    def __new__(
        cls,
        obs_lists: ObservationLists,
        max_hyper: int  ,   
    ):
    
        def __init__(self):
            E = Encoding()
            self.max_hyper = max_hyper
            self.obs_lists= obs_lists
            
            self.encode()

        #decision propositions layer 0
    """
         pre0(a,mk) # meta-feature mk appears negated in precondition of action a
         pre1(a,mk) # meta-feature mk appears positive in precondition of action a
         eff0(a,mk) # meta-feature mk appears negated in effect of action a
         eff1(a,mk) # meta-feature mk appears positive in effect of action a
         label(a,l) # action a is mapped to label l

         arity(p,i) # atom p has arity i
         atom2(mk,p) # meta-feature mk is atom p, arg2
        (mk,i,mo) # meta-object mo is mapped to i-th arg of meta-feature mk, arg3
         unary(u,a,mo) # action a uses static unary predicate u on argument mo
         binary(b,a,mo,mo') # action a uses static binary predicate b on arguments mo and mo
         
         args(a,mo) # meta-object mo is argument of action a
         relevant(a,mo,mk,i) # using(a,mk) & atom(mk,i,mo)
         using(mk) # meta-feature mk is used by some action
         using(a,mk) # meta-feature mk is used by action a
    """
    def encode(self):

        @dataclass
        @proposition(E)
        class PRE0(Hashable):
            m: int # atom name
            a: str # action name 

            def __str__(self):
                return f"pre0({self.a},{self.m})"

        
        @dataclass
        @proposition(E)
        class PRE1(Hashable):
            m: str # atom name
            a: str # action name 

            def __str__(self):
                return f"pre1({self.a},{self.m})"

        
        @dataclass
        @proposition(E)
        class EFF0(Hashable):
            m: str # atom name
            a: str # action name 

            def __str__(self):
                return f"eff0({self.a},{self.m})"

        @dataclass
        @proposition(E)
        class EFF1(Hashable):
            m: str # atom name
            a: str # action name 

            def __str__(self):
                return f"eff1({self.a},{self.m})"

        
        @dataclass
        @proposition(E)
        class LABEL(Hashable):
            l: str # label name
            a: str # action name 

            def __str__(self):
                return f"label({self.a},{self.l})"

        @dataclass
        @proposition(E)
        class ARITY(Hashable):
            p: int # predicate id
            a: str # action name 

            def __str__(self):
                return f"arity({self.p},{self.l})"

        @dataclass
        @proposition(E)
        class AT2(Hashable):
            p: int # predicate ID
            m: str # atom name

            def __str__(self):
                return f"at2({self.m},{self.p})"

        @dataclass
        @proposition(E)
        class AT3(Hashable):
            v: int # argument num of action
            m: str # atom name
            i: int # argument num of atom


            def __str__(self):
                return f"at3({self.m},{self.i},{self.v})" 

        @dataclass
        @proposition(E)
        class UN(Hashable):
            u: int # unary predicate
            a: str # action name 
            v: int # argument num of action


            def __str__(self):
                return f"un({self.u},{self.a},{self.v})"   

        @dataclass
        @proposition(E)
        class BIN(Hashable):
            b: int # binary predicate
            a: str # action name 
            v: int # argument num of action
            v1: int # argument num of action


            def __str__(self):
                return f"bin({self.b},{self.a},{self.v},{self.v1})"                

        #implied propositions layer 0
        @dataclass
        @proposition(E)
        class USE1(Hashable):
            m: str # atom name

            def __str__(self):
                return f"use1({self.m})" 

        @dataclass
        @proposition(E)
        class USE2(Hashable):
            m: str # atom name
            a: str # action name 

            def __str__(self):
                return f"use2({self.a},{self.m})"

        @dataclass
        @proposition(E)
        class ARG(Hashable):
            v: int # argument num
            a: str # action name 

            def __str__(self):
                return f"arg({self.a},{self.v})"

        @dataclass
        @proposition(E)
        class ARGVAL(Hashable):
            v: int # argument num
            a: str # action name 
            m: str # atom name
            i: int # argument num of atom

            def __str__(self):
                return f"argval({self.a},{self.v},{self.m},{self.i})" 

        
        #decision propositions instance layer

        @dataclass
        @proposition(E)
        class MP(Hashable):
            a: str # action name 
            t: str # transition name corresponding to edge

            def __str__(self):
                return f"mp({self.t},{self.a})" 

        @dataclass
        @proposition(E)
        class MF(Hashable):
            m: str # atom name
            k: str # ground atom name   
            t: str # transition name corresponding to edge

            def __str__(self):
                return f"mf({self.t},{self.k},{self.m})" 

        @dataclass
        @proposition(E)
        class PHI(Hashable):
            k: str # ground atom name   
            s: str # state name corresponding to node 

            def __str__(self):
                return f"phi({self.k},{self.s}" 

        @dataclass
        @proposition(E)
        class GR2(Hashable):
            k: str # ground atom name   
            p: int # predicate ID
            def __str__(self):
                return f"gr2({self.k},{self.p}" 
        
        @dataclass
        @proposition(E)
        class GR3(Hashable):
            k: str # ground atom name   
            i: int # argument num of atom
            o: int # object id 
            def __str__(self):
                return f"gr3({self.k},{self.p}"

        @dataclass
        @proposition(E)
        class R(Hashable):
            u: int # unary predicate
            o: int # object id 
            def __str__(self):
                return f"r({self.u},{self.o}"       

        @dataclass
        @proposition(E)
        class S(Hashable):
            b: int # binary predicate
            o: int # object id 
            o1: int #object id 
            def __str__(self):
                return f"s({self.b},{self.o},{self.o1}"

        @dataclass
        @proposition(E)
        class GTUPLE(Hashable):
            a: str # action name 
            o2: tuple # tuple of objects 
            def __str__(self):
                return f"gtuple({self.a},{self.o2}"
        
        @dataclass
        @proposition(E)
        class FREE(Hashable):
            a: str # action name 
            k: str # ground atom name   
            t: str # transition name corresponding to edge
            def __str__(self):
                return f"free({self.k},{self.t},{self.a}"

        @dataclass
        @proposition(E)
        class G(Hashable):
            k: str # ground atom name   
            s: str # state name corresponding to node 
            s1: str # state name corresponding to node 

            def __str__(self):
                return f"g({self.k},{self.s},{self.s1}" 

        @dataclass
        @proposition(E)
        class U(Hashable):
            u: int # unary predicate
            a: str # action name
            v: int # argument num
            o: int # object id

            def __str__(self):
                return f"u({self.u},{self.a},{self.v},{self.o}"

        @dataclass
        @proposition(E)
        class B(Hashable):
            b: int # binary predicate
            a: str # action name
            v: int # argument num
            v1: int # argument num
            o: int # object id
            o1: int # object id

            def __str__(self):
                return f"b({self.b},{self.a},{self.v},{self.v1},{self.o},{self.o1}"         

        @dataclass
        @proposition(E)
        class MT(Hashable):
            t: str # transition name corresponding to edge
            v: int # argument num
            o: int # object id

            def __str__(self):
                return f"mt({self.t},{self.v},{self.o}" 

        @dataclass
        @proposition(E)
        class W(Hashable):
            t: str # transition name corresponding to edge
            k: str # ground atom name  
            i: int # argument num of atom
            v: int # argument num

            def __str__(self):
                return f"w({self.t},{self.k},{self.i},{self.v}" 

        @dataclass
        @proposition(E)
        class G(Hashable):
            t: str # transition name corresponding to edge
            a: str # action name
            o2: tuple # tuple of objects

            def __str__(self):
                return f"g({self.t},{self.a},{self.o2}" 

        @dataclass
        @proposition(E)
        class APP1(Hashable):
            a: str # action name
            s: str # state name corresponding to node
            o2: tuple # tuple of objects 

            def __str__(self):
                return f"app1({self.a},{self.o2},{self.s}" 

        @dataclass
        @proposition(E)
        class VIO0(Hashable):
            a: str # action name
            s: str # state name corresponding to node
            o2: tuple # tuple of objects
            k: str # ground atom name  

            def __str__(self):
                return f"vio0({self.a},{self.o2},{self.s},{self.k}" 

        @dataclass
        @proposition(E)
        class VIO1(Hashable):
            a: str # action name
            s: str # state name corresponding to node
            o2: tuple # tuple of objects
            k: str # ground atom name  

            def __str__(self):
                return f"vio1({self.a},{self.o2},{self.s},{self.k}" 

        @dataclass
        @proposition(E)
        class PRE0EQ(Hashable):
            a: str # action name
            m: str # atom name
            o2: tuple # tuple of objects
            k: str # ground atom name  

            def __str__(self):
                return f"pre0eq({self.a},{self.o2},{self.k},{self.m}" 

        @dataclass
        @proposition(E)
        class PRE1EQ(Hashable):
            a: str # action name
            m: str # atom name
            o2: tuple # tuple of objects
            k: str # ground atom name  

            def __str__(self):
                return f"pre1eq({self.a},{self.o2},{self.k},{self.m}"

        @dataclass
        @proposition(E)
        class EQ(Hashable):
            m: str # atom name
            o2: tuple # tuple of objects
            k: str # ground atom name  

            def __str__(self):
                return f"eq({self.o2},{self.m},{self.k}"


    def constraits_layer0():

        def precond_and_effect():
            """
            use(a, m)⇔p0(a, m)∨p1(a, m)∨e0(a, m)∨e1(a, m) (2)
            use(m) ⇔ use(a, m) (3)
            ¬p0(a, m) ∨ ¬p1(a, m) (4)
            ¬e0(a, m) ∨ ¬e1(a, m) (5)
            At-Most-1 {label(a, l) : l} (6)
            """
            pass
        
        def effects_nonred():

            """
            e0(a, m) ⇒ ¬p0(a, m) (7)
            e1(a, m) ⇒ ¬p1(a, m) (8)
            Exactly-1 {arity(p, i) : 0 ≤ i ≤ max-arity} (9)
            """
            pass
        
        def struct_of_atom():

            """
            Exactly-1 {at(m, p) : p} (10)
            At-Most-1 {at(m, i, ν) : ν} (11)
            at(m, p) ∧ at(m, i, ν) ⇒arity(p, j) (12)
            at(m, p) ∧ arity(p, i) ⇒at(m, j, ν) (13)
            at(m, p) ∧ arity(p, i) ⇒ ¬at(m, j, ν) (14)
            """
            pass
        
        def atomname_to_atomstruct():
            """
            Strict-Lex-Order {vect(m) : m} (15)
            """
            pass
        
        def atoms_nonstatic():
            """
            ¬static0(a, m, p) ∨ ¬static1(a, m, p)(16)
            ¬static0(a, m, p) ⇒ at(m, p) ∧ p1(a, m) ∧ e0(a, m) (17)
            ¬static1(a, m, p) ⇒ at(m, p) ∧ p0(a, m) ∧ e1(a, m) (18)
            """
            pass
        
        def atom_act_arg():
            """
            use(a, m) ∧ at(m, i, ν) ⇒ arg(a, ν) (19)
            arg(a, ν) ⇒ argval(a, ν, m, i) (20)
            argval(a, ν, m, i) ⇔ use(a, m) ∧ at(m, i, ν) (21)
            """
            pass
        
        def arity_act_and_pred():
            """
             ¬arg(a, ν) (22)
             arg(a, ν) (23)
             ¬arity(p, i) ∧arity(p, i) (24)
            """
            pass
        
        def staticpred_actarg():
            """
            un(u, a, ν) ⇒ arg(a, ν) (25)
            bin(b, a, ν, ν0) ⇒ arg(a, ν) ∧ arg(a, ν') (26)
            """
            pass

    def constraits_layer1():

        def binding_transitions():
            """
            Exactly-1 {mp(t, a) : a} (27)
            At-Most-1 {mf(t, k, m) : m} (28)
            At-Most-1 {mf(t, k, m) : k} (29)
            """
            pass
        
        def consistancy():

            """
            mp(t, a) ⇒ label(a, t.label) (30)
            mp(t, a) ∧ mf(t, k, m) ⇒ use(a, m) (31)
            mp(t, a) ∧ use(a, m) ⇒ mf(t, k, m) (32)
            
            """
            pass
        
        def ground_atom_unaff():

            """
            mp(t, a) ∧ ¬mf(t, k, m) ⇒ free(k, t, a) (33)
            mp(t, a) ∧ mf(t, k, m) ⇒ ¬e0(a, m) ∧ ¬e1(a, m) ⇔ free(k, t, a) (34)
            """
            pass
        
        def trans_and_inertia():
            """
            mp(t, a) ∧ mf(t, k, m) ∧ p0(a, m) ⇒ ¬φ(k, t.src) (35)
            mp(t, a) ∧ mf(t, k, m) ∧ p1(a, m) ⇒ φ(k, t.src) (36)
            mp(t, a) ∧ mf(t, k, m) ∧ e0(a, m) ⇒ ¬φ(k, t.dst) (37)
            mp(t, a) ∧ mf(t, k, m) ∧ e1(a, m) ⇒ φ(k, t.dst) (38)
            mp(t, a)⇒ free(k, t, a)⇔[φ(k, t.src)⇔φ(k, t.dst)](39)
            """
            pass
        
        def groundatom_differvalue():
            """
            g(k, s, s') ⇔ φ(k, s) ⊕ φ(k, s') (40)
            g(k, s, s0) (41)
            """
            pass
        
        def groundatom_pre_arg():
            """
            Exactly-1 {gr(k, p) : p} (42)
            At-Most-1 {gr(k, i, o) : o} (43)
            gr(k, p) ∧ gr(k, i, o) ⇒ arity(p, j) (44)
            gr(k, p) ∧ arity(p, i) ⇒ gr(k, j, o) (45)
            gr(k, p) ∧ arity(p, i) ⇒ ¬gr(k, j, o) (46)
            """
            pass
        
        def groundatom_to_arg_and_pred():
            """
            Strict-Lex-Order {vect(k) : k} (47)
            """
            pass
        
        def sync_groundatom_and_schema():
            """
            mf(t, k, m) ⇒ at(m, p) ⇔ gr(k, p) (48)
            mf(t, k, m) ∧ at(m, i, ν) ⇒ gr(k, i, o) (49)
            mf(t, k, m) ∧ gr(k, i, o) ⇒ at(m, i, ν) (50)
            """
            pass

        def exclusive_binding_statpred():
            """
            U(u, a, ν, o) ⇔ un(u, a, ν) ∧ ¬r(u, o) (51)
            B(b, a, ν, ν', o, o') ⇔ bin(b, a, ν, ν')∧ ¬s(b, o, o') (52)
            """
            pass


        def assoc_binding_transitions_pt1():
            """
            At-Most-1 {mt(t, ν, o) : o} (53)
            mp(t, a) ∧ arg(a, ν) ⇒ mt(t, ν, o) (54)
            mp(t, a) ∧ mt(t, ν, o) ⇒ arg(a, ν) (55)
            """
            pass

        def assoc_binding_transitions_pt2():
            """
            mf(t, k, m) ∧ at(m, i, ν) ⇒ W(t, k, i, ν) (56)
            W(t, k, i, ν) ⇒ gr(k, i, o) ⇔ mt(t, ν, o) (57)
            """
            pass

        def nonexist_gtuple():
            """
            ¬gtuple(a, o¯) ⇒ ¬arg(a, νi) ∨ U(u, a, νi, oi) ∨ B(b, a, νi, νj , oi, oj ) (58)
            """
            pass

        def exist_groundatom():
            """
            mp(t, a) ∧ mt(t, ν, o) ∧ un(u, a, ν) ⇒ r(u, o) (59)
            mp(t, a) ∧ mt(t, ν, o) ∧ mt(t, ν', o') ∧ bin(b, a, ν, ν') (60) ⇒ s(b, o, o') (61)
            """
            pass

        def groundaction_tran_mandate():
            """
            gtuple(a, o¯) ⇒G(t, a, o¯) (62)
            G(t, a, o¯) ⇒ gtuple(a, o¯) (63)
            G(t, a, o¯) ⇒ mp(t, a) ∧ mt(t, νi, oi) ∧ arg(a, νi) ⇒ mt(t, νi, oi) (64)
            At-Most-1 {G(t, a, o¯) : t.src # s} (65)
            Exactly-1 {G(t, a, o¯) : a, o¯} (66)
            """
            pass

        def app_actions_mandate():
            """
            G(t, a, o¯) ⇒ appl(a, o, t.src ¯ ) (67)
            appl(a, o, s  ) ⇒ G(t, a, o¯) (68)
            ¬appl(a, o, s ¯ ) ⇒ ¬gtuple(a, o¯) ∨ vio0(a, o, s, k ¯ ) ∨ vio1(a, o, s, k ¯ ) (69)
            vio0(a, o, s, k ¯ ) ⇒ φ(k, s) ∧ pre0eq(a, o, k, m ¯ ) (70)
            vio1(a, o, s, k ¯ ) ⇒ ¬φ(k, s) ∧ pre1eq(a, o, k, m ¯ ) (71)
            pre0eq(a, o, k, m ¯ ) ⇒ p0(a, m) ∧ eq(¯o, m, k) (72)
            pre1eq(a, o, k, m ¯ ) ⇒ p1(a, m) ∧ eq(¯o, m, k) (73)
            eq(¯o, m, k) ⇒ at(m, p) ⇔ gr(k, p) (74)
            eq(¯o, m, k) ∧ at(m, i, νj ) ⇒ gr(k, i, oj ) (75)
            """
            pass
        
        


        return Model
    


from typing import List, Set
from collections import defaultdict
from macq.extract import Model
from attr import dataclass
from bauhaus import Encoding, constraint, proposition

e = Encoding()

class BGLearner:
    """ max arity for atom schema
        atom schemas: p0, p1, ...
        max arity for action schema (defines meta-objects: mo0, mo1, ...)
        action schemas: a0, a1, ...
        meta-features: mk0, mk1, ...
        num unary predicates: u0, u1, ... (unary preds)
        num binary predicates: b0, b1, ... (binary preds)
        """

    def __new__(
        cls,
        obs_lists: ObservationLists,
        max_hyper: int,
        action(x):x=num_act
        arity
        predicate
        m
        arg    
    ):

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
        
        def staticpred_actarg():
            """
            mf(t, k, m) ⇒ at(m, p) ⇔ gr(k, p) (48)
            mf(t, k, m) ∧ at(m, i, ν) ⇒ gr(k, i, o) (49)
            mf(t, k, m) ∧ gr(k, i, o) ⇒ at(m, i, ν) (50)
            """
            pass

        def precond_and_effect():
            """
            U(u, a, ν, o) ⇔ un(u, a, ν) ∧ ¬r(u, o) (51)
            B(b, a, ν, ν', o, o') ⇔ bin(b, a, ν, ν')∧ ¬s(b, o, o') (52)
            """
            pass


         def precond_and_effect():
            """
            At-Most-1 {mt(t, ν, o) : o} (53)
            mp(t, a) ∧ arg(a, ν) ⇒ mt(t, ν, o) (54)
            mp(t, a) ∧ mt(t, ν, o) ⇒ arg(a, ν) (55)
            """
            pass

         def precond_and_effect():
            """
            mf(t, k, m) ∧ at(m, i, ν) ⇒ W(t, k, i, ν) (56)
            W(t, k, i, ν) ⇒ gr(k, i, o) ⇔ mt(t, ν, o) (57)
            """
            pass

         def precond_and_effect():
            """
            ¬gtuple(a, o¯) ⇒ ¬arg(a, νi) ∨ U(u, a, νi, oi) ∨ B(b, a, νi, νj , oi, oj ) (58)
            """
            pass

         def precond_and_effect():
            """
            mp(t, a) ∧ mt(t, ν, o) ∧ un(u, a, ν) ⇒ r(u, o) (59)
            mp(t, a) ∧ mt(t, ν, o) ∧ mt(t, ν', o') ∧ bin(b, a, ν, ν') (60) ⇒ s(b, o, o') (61)
            """
            pass

         def precond_and_effect():
            """
            gtuple(a, o¯) ⇒G(t, a, o¯) (62)
            G(t, a, o¯) ⇒ gtuple(a, o¯) (63)
            G(t, a, o¯) ⇒ mp(t, a) ∧ mt(t, νi, oi) ∧ arg(a, νi) ⇒ mt(t, νi, oi) (64)
            At-Most-1 {G(t, a, o¯) : t.src = s} (65)
            Exactly-1 {G(t, a, o¯) : a, o¯} (66)
            """
            pass

         def precond_and_effect():
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
    

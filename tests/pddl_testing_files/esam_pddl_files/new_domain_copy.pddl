
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Domain file automatically generated by the Tarski FSTRIPS writer
;;; 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define (domain logistics)
    (:requirements :typing)
    (:types
        loc - object
        cit - object
        obj - object
        object
    )

    (:constants
        
    )

    (:predicates
        (location ?x1 - loc)
        (in-city ?x1 - loc ?x2 - cit)
        (airport ?x1 - loc)
        (airplane ?x1 - obj)
        (in ?x1 - obj ?x2 - obj)
        (package ?x1 - obj)
        (city ?x1 - cit)
        (at ?x1 - obj ?x2 - loc)
        (truck ?x1 - obj)
    )

    (:functions
        
    )

    

    
    (:action load-airplane_5_1
     :parameters (?x0 - obj ?x1 - obj ?x2 - loc)
     :precondition (and (at ?x0 ?x2) (airport ?x2) (location ?x2) (at ?x1 ?x2) (package ?x0) (airplane ?x1))
     :effect (and
        (in ?x0 ?x1)
        (not (at ?x0 ?x2)))
    )


    (:action drive-truck_1_1
     :parameters (?x0 - obj ?x1 - loc ?x2 - loc ?x3 - cit)
     :precondition (and (truck ?x0) (in-city ?x1 ?x3) (location ?x2) (city ?x3) (location ?x1) (in-city ?x2 ?x3) (at ?x0 ?x1))
     :effect (and
        (at ?x0 ?x2)
        (not (at ?x0 ?x1)))
    )


    (:action fly-airplane_2_1
     :parameters (?x0 - obj ?x1 - loc ?x2 - loc)
     :precondition (and (airport ?x2) (location ?x2) (location ?x1) (airport ?x1) (airplane ?x0) (at ?x0 ?x1))
     :effect (and
        (at ?x0 ?x2)
        (not (at ?x0 ?x1)))
    )


    (:action unload-truck_4_1
     :parameters (?x0 - obj ?x1 - obj ?x2 - loc)
     :precondition (and (truck ?x1) (location ?x2) (at ?x1 ?x2) (in ?x0 ?x1) (package ?x0))
     :effect (and
        (at ?x0 ?x2)
        (not (in ?x0 ?x1)))
    )


    (:action load-truck_3_1
     :parameters (?x0 - obj ?x1 - obj ?x2 - loc)
     :precondition (and (truck ?x1) (at ?x0 ?x2) (location ?x2) (at ?x1 ?x2) (package ?x0))
     :effect (and
        (in ?x0 ?x1)
        (not (at ?x0 ?x2)))
    )

)
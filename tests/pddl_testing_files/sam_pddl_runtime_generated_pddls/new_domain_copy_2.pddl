
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; Domain file automatically generated by the Tarski FSTRIPS writer
;;; 
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define (domain logistics)
    (:requirements :typing)
    (:types
        obj - object
        loc - object
        cit - object
        object
    )

    (:constants
        
    )

    (:predicates
        (package ?x1 - obj)
        (at ?x1 - obj ?x2 - loc)
        (in-city ?x1 - loc ?x2 - cit)
        (airport ?x1 - loc)
        (truck ?x1 - obj)
        (city ?x1 - cit)
        (airplane ?x1 - obj)
        (location ?x1 - loc)
        (in ?x1 - obj ?x2 - obj)
    )

    (:functions
        
    )

    

    
    (:action load-airplane
     :parameters (?x0 - obj ?x1 - obj ?x2 - loc)
     :precondition (and (location ?x2) (airplane ?x1) (at ?x0 ?x2) (at ?x1 ?x2) (package ?x0))
     :effect (and
        (in ?x0 ?x1)
        (not (at ?x0 ?x2)))
    )


    (:action unload-airplane
     :parameters (?x0 - obj ?x1 - obj ?x2 - loc)
     :precondition (and (location ?x2) (airplane ?x1) (in ?x0 ?x1) (at ?x1 ?x2) (package ?x0))
     :effect (and
        (at ?x0 ?x2)
        (not (in ?x0 ?x1)))
    )


    (:action load-truck
     :parameters (?x0 - obj ?x1 - obj ?x2 - loc)
     :precondition (and (location ?x2) (at ?x0 ?x2) (at ?x1 ?x2) (truck ?x1) (package ?x0))
     :effect (and
        (in ?x0 ?x1)
        (not (at ?x0 ?x2)))
    )


    (:action fly-airplane
     :parameters (?x0 - obj ?x1 - loc ?x2 - loc)
     :precondition (and (airport ?x1) (airplane ?x0) (airport ?x2) (at ?x0 ?x1))
     :effect (and
        (at ?x0 ?x2)
        (not (at ?x0 ?x1)))
    )


    (:action unload-truck
     :parameters (?x0 - obj ?x1 - obj ?x2 - loc)
     :precondition (and (location ?x2) (in ?x0 ?x1) (at ?x1 ?x2) (truck ?x1) (package ?x0))
     :effect (and
        (at ?x0 ?x2)
        (not (in ?x0 ?x1)))
    )


    (:action drive-truck
     :parameters (?x0 - obj ?x1 - loc ?x2 - loc ?x3 - cit)
     :precondition (and (location ?x2) (in-city ?x1 ?x3) (city ?x3) (location ?x1) (at ?x0 ?x1) (truck ?x0) (in-city ?x2 ?x3))
     :effect (and
        (at ?x0 ?x2)
        (not (at ?x0 ?x1)))
    )

)
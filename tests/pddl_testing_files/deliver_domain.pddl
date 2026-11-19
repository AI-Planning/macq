(define (domain Deliver)
  (:requirements :strips :typing)
  (:types
    location locatable - object
    vehicle package - locatable
    truck - vehicle)
  (:predicates
    (at ?x - locatable ?l - location)
    (in ?p - package ?v - vehicle)
    (road ?a ?b - location))
  (:action drive
    :parameters (?t - truck ?a ?b - location)
    :precondition (and (at ?t ?a) (road ?a ?b))
    :effect (and (at ?t ?b) (not (at ?t ?a))))
  (:action load
    :parameters (?p - package ?v - vehicle ?l - location)
    :precondition (and (at ?p ?l) (at ?v ?l))
    :effect (and (in ?p ?v) (not (at ?p ?l))))
  (:action unload
    :parameters (?p - package ?v - vehicle ?l - location)
    :precondition (and (in ?p ?v) (at ?v ?l))
    :effect (and (at ?p ?l) (not (in ?p ?v)))))

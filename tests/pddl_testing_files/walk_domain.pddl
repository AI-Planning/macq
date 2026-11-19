(define (domain WalkTest)
  (:requirements :strips :typing :negative-preconditions :equality)
  (:types Room Key - object)
  (:predicates
    (At ?r - Room)
    (Linked ?a ?b - Room)
    (KeyIn ?k - Key ?r - Room)
    (Holding ?k - Key))
  (:action Move
    :parameters (?a ?b - Room)
    :precondition (and (At ?a) (Linked ?a ?b) (not (= ?a ?b)))
    :effect (and (At ?b) (not (At ?a))))
  (:action Grab
    :parameters (?k - Key ?r - Room)
    :precondition (and (At ?r) (KeyIn ?k ?r) (not (Holding ?k)))
    :effect (and (Holding ?k) (not (KeyIn ?k ?r))))
  (:action Drop
    :parameters (?k - Key ?r - Room)
    :precondition (and (At ?r) (Holding ?k))
    :effect (and (KeyIn ?k ?r) (not (Holding ?k)))))

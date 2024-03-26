;; logistics domain
;;

(define (domain graph)
  (:requirements :strips)
  (:types object)
  (:predicates
  (vertex ?obj - object)
    (has-edge ?v1 - object ?v2 - object))

(:action add-edge
  :parameters
   (?v1
    ?v2)
  :precondition
   (and (vertex ?v1) (vertex ?v2)
	(not(has-edge ?v1 ?v2)))
  :effect
   (has-edge ?v1 ?v2))

(:action remove-edge
  :parameters
   (?v1
    ?v2)
  :precondition
   (and (vertex ?v1) (vertex ?v2)
	(has-edge ?v1 ?v2))
  :effect
   (not(has-edge ?v1 ?v2)))
)
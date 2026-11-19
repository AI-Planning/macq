(define (problem deliver-1)
  (:domain Deliver)
  (:objects
    t1 - truck
    p1 p2 - package
    l1 l2 l3 - location)
  (:init
    (at t1 l1)
    (at p1 l1)
    (at p2 l2)
    (road l1 l2)
    (road l2 l1)
    (road l2 l3)
    (road l3 l2))
  (:goal (and (at p1 l3) (at p2 l1))))

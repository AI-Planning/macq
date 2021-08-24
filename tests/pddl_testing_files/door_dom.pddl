(define (domain door)

    (:requirements :strips )

    (:predicates
        (roomA ) (roomB ) (open )
    )

    (:action open
        :parameters ( )
        :precondition (and (roomA ))
        :effect (and (open ))
    )
    
    (:action walk
        :parameters ( )
        :precondition (and (roomA ) (open ))
        :effect (and (not (roomA )) (roomB ))
    )
)
class Predicate:
    def __init__(self, name, objects):
        """
        Class to handle a predicate and the objects it is applied to.

        Arguments
        ---------
        name : string
            The name of the predicate.
        objects : list
            The list of objects this predicate applies to.
        """
        self.name = name
        self.objects = objects
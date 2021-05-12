class Predicate:
    def __init__(self, name, objects):
        """Class to handle a predicate and the objects it is applied to"""
        # name of the predicate
        self.name = name
        # assign objects it is applied to
        self.objects = []
        for obj in objects:
            self.objects.append(obj)
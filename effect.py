from predicate import Predicate

class Effect(Predicate):
    def __init__(self, name, objects, func, probability=100):
        """
        Class to handle an individual effect of an action.
                
        Arguments
        ---------
        name : string
            The name of the effect.
        objects : list
            The list of objects this effect applies to.
        func : string
            The name of the function that applies the effect in the corresponding action.
        probability : int
            For non-deterministic problems, the probability that this effect will take place
            (defaults to 100)
        """
        super().__init__(name, objects)
        self.func = func
        self.probability = self.set_prob(probability)
        
    def set_prob(self, prob):
        """
        Setter function for probability.

        Arguments
        ---------
        prob : int
            The probability to be assigned.

        Returns
        -------
        prob : int
            The probability, after being checked for validity.
        """
        # ensure an integer is given
        try:
            test_int = int(prob)
        except ValueError:
            raise ValueError("Must enter an integer value for probability.")
        # enforce that probability is between 0 and 100 inclusive
        if prob < 0:
            prob = 0
        elif prob > 100:
            prob = 100
        return prob
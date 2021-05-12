class Effect:
    def __init__(self, name, func, probability=100):
        """Class to handle an individual effect of an action"""
        # name of the effect
        self.name = name
        # function to apply the effect in the corresponding action
        self.func = func
        # for non-deterministic problems, the probability this effect will take place (defaults to 100)
        self.prob = self.set_prob(probability)
        
    def set_prob(self, prob):
        """Setter function for probability"""
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

import bauhaus
class BGLearner:
     class InvalidThreshold(Exception):
        def __init__(self, threshold):
            super().__init__(
                f"Invalid threshold value: {threshold}. Threshold must be a float between 0-1 (inclusive)."
            )


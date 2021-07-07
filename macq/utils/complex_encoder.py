from json import JSONEncoder


class ComplexEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "_serialize"):
            return obj._serialize()
        else:
            return JSONEncoder.default(self, obj)

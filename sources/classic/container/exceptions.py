
class ResolutionError(BaseException):

    def __init__(self):
        self.stack = []

    def add(self, **kwargs: object):
        self.stack.append(str(kwargs))

    def __str__(self):
        return str(self.stack)

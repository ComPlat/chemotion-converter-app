class Writer(object):

    def __init__(self, converter):
        raise NotImplementedError

    def write(self):
        return self.buffer.getvalue()

    def process(self):
        raise NotImplementedError

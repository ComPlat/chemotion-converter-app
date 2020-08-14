class Writer(object):

    def __init__(self, buffer):
        self.buffer = buffer

    def write(self, data):
        raise NotImplementedError

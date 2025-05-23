class Writer(object):

    def __init__(self, converter):
        self.converter = converter

    def write(self):
        return self.buffer.getvalue()

    def process(self):
        raise NotImplementedError

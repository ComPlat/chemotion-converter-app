import io


class Writer(object):

    def __init__(self):
        self.buffer = io.StringIO()

    def write(self):
        return self.buffer.getvalue()

    def process(self, metadata, data):
        raise NotImplementedError

    @property
    def options(self):
        raise NotImplementedError

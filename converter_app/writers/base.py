class Writer(object):

    def write(self):
        return self.buffer.getvalue()

    def process(self, metadata, data):
        raise NotImplementedError

    @property
    def options(self):
        raise NotImplementedError

    @property
    def suffix(self):
        raise NotImplementedError

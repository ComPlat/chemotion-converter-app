class Reader(object):

    def check(self):
        raise NotImplementedError

    def process(self):
        raise NotImplementedError

    def convert_to_json(self):
        raise NotImplementedError

    def __init__(self, file):
        self.file = file

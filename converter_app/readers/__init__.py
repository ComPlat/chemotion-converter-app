from .csv import CSVReader
from .txt import TXTReader


class Readers:

    def __init__(self):
        self._registry = {
            'readers': {},
        }

    def register(self, reader):
        if reader.identifier in self._registry['readers']:
            raise ValueError('Identifier ({}) is already registered'
                             .format(reader.identifier))
        self._registry['readers'][reader.identifier] = reader

    @property
    def readers(self):
        return self._registry['readers']

    def match_reader(self, file):
        for identifier, reader in self.readers.items():
            reader = reader(file)
            if reader.check():
                return reader


registry = Readers()
registry.register(CSVReader)
registry.register(TXTReader)

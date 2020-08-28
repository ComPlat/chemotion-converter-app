from .ascii import AsciiReader
from .csv import CSVReader


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

    def match_reader(self, file, file_name, content_type):
        for identifier, reader in self.readers.items():
            reader = reader(file, file_name, content_type)
            if reader.check():
                return reader


registry = Readers()
registry.register(CSVReader)
registry.register(AsciiReader)

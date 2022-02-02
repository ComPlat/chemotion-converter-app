import logging
from collections import OrderedDict

from .ascii import AsciiReader
from .csv import CSVReader
from .excel import ExcelReader
from .brml import BrmlReader
from .dta import DtaReader

logger = logging.getLogger(__name__)


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
        sorted_readers = sorted(self._registry['readers'].values(), key=lambda reader: reader.priority)
        return OrderedDict([(reader.identifier, reader) for reader in sorted_readers])

    def match_reader(self, file, file_name, content_type):
        for identifier, reader in self.readers.items():
            reader = reader(file, file_name, content_type)
            result = reader.check()

            # reset file pointer and return the reader it is the one
            file.seek(0)
            if result:
                return reader


registry = Readers()
registry.register(CSVReader)
registry.register(AsciiReader)
registry.register(ExcelReader)
registry.register(BrmlReader)
registry.register(DtaReader)

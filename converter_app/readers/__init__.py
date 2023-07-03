import logging
from collections import OrderedDict

from .asc_zip import AscZipReader
from .aif import AifReader
from .ascii import AsciiReader
from .brml import BrmlReader
from .cary import CaryReader
from .cif import CifReader
from .csv import CSVReader
from .dsp import DSPReader
from .dta import DtaReader
from .excel import ExcelReader
from .jasco import JascoReader
from .nova import NovaReader
from .pssession import PsSessionReader
from .sec import SecReader
from .sem import SemReader
from .gcd import GcdReader

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

    def match_reader(self, file):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     file.name, file.content_type, file.mime_type, file.encoding)

        for identifier, reader in self.readers.items():
            reader = reader(file)
            result = reader.check()

            # reset file pointer and return the reader it is the one
            file.fp.seek(0)
            if result:
                return reader


registry = Readers()
registry.register(AifReader)
registry.register(AsciiReader)
registry.register(BrmlReader)
registry.register(CaryReader)
registry.register(CifReader)
registry.register(CSVReader)
registry.register(DSPReader)
registry.register(DtaReader)
registry.register(ExcelReader)
registry.register(JascoReader)
registry.register(NovaReader)
registry.register(PsSessionReader)
registry.register(SecReader)
registry.register(AscZipReader)
registry.register(SemReader)
registry.register(GcdReader)

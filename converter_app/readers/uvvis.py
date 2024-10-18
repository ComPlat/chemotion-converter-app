import logging

from converter_app.readers.helper.reader import Readers
from converter_app.readers.csv_reader import CSVReader

logger = logging.getLogger(__name__)


class UvvisReader(CSVReader):
    """
    Uvvis Reader class.  It extends converter_app.readers.ascii.CSVReader
    """

    identifier = 'uvvis_reader'
    priority = 10

    def __init__(self, file):
        super().__init__(file)
        self.metadata_lines = None
        self.lines = None
        self.rows = None

    def check(self):
        """
        :return: True if it fits
        """
        result = super().check()
        if result:
            metadata_begin = self.lines[-2]
            return 'Properties' in metadata_begin

        return result

    def prepare_tables(self):
        tables = super().prepare_tables()
        metadata_content = self.lines[-1]
        key = ''
        value = ''
        for s in metadata_content.split('\t'):
            if '#' in s:
                key = s[5:]
            else:
                value = s
            tables[0]['metadata'][key] = value
        return tables


Readers.instance().register(UvvisReader)

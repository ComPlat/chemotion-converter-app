import logging

from converter_app.readers.helper.reader import Readers
from converter_app.readers.ascii import AsciiReader

logger = logging.getLogger(__name__)


class AifReader(AsciiReader):
    """
    Afi Reader class.  It extends converter_app.readers.ascii.AsciiReader
    """
    identifier = 'aif_reader'
    priority = 95

    def check(self):
        """
        :return: True if it fits
        """
        if self.file.suffix.lower() in ('.txt','.aif') and self.file.mime_type == 'text/plain':
            first_line = self.file.string.splitlines()[0]
            return 'raw2aif' in first_line

        return False

    def prepare_tables(self):
        tables = super().prepare_tables()
        for table in tables:
            unit_counter = 0
            unit_section = False
            for entry in table['header']:
                entry_kv = entry.split()
                if len(entry_kv) >= 2:
                    table['metadata'][entry_kv[0]] = ' '.join(entry_kv[1:]).replace("'", '')
                elif entry.startswith('loop'):
                    unit_counter = 0
                    unit_section = True
                elif unit_section:
                    table['metadata'][f'Unit_column_#{unit_counter}'] = entry
                    unit_counter = unit_counter + 1
                else:
                    unit_section = False

        return tables


Readers.instance().register(AifReader)

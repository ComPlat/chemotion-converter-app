import logging

from .ascii import AsciiReader

logger = logging.getLogger(__name__)


class AifReader(AsciiReader):
    identifier = 'aif_reader'
    priority = 95

    def check(self):
        result = False
        if self.file.suffix.lower() == '.txt' and self.file.mime_type == 'text/plain':
            first_line = self.file.string.splitlines()[0]
            result = 'raw2aif' in first_line

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = super(AifReader, self).get_tables()
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
                    table['metadata']['Unit_column_#%d' % unit_counter] = entry
                    unit_counter = unit_counter + 1
                else:
                    unit_section = False

        return tables

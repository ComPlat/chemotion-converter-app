import logging
import re

from pathlib import Path

from .base import Reader

logger = logging.getLogger(__name__)


class DtaReader(Reader):
    identifier = 'dta_reader'
    priority = 10

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        if self.encoding == 'binary':
            result = False
        elif Path(self.file_name).suffix.lower() == '.dta' and self.mime_type == 'text/plain':
            result = True
        else:
            result = False

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        count = 0
        tables = []
        self.append_table(tables)

        # loop over lines of the file
        for line in self.file.readlines():
            row = line.decode(self.encoding).rstrip()

            if row.startswith('\t'):
                count += 1

                if count < 3:
                    # add the first 2 rows to the header
                    tables[-1]['header'].append(row)
                else:
                    tables[-1]['rows'].append([self.get_value(value) for value in row.split()])
            else:
                # this is the header
                if tables[-1]['rows']:
                    # if a table is already there, this must be a new header
                    self.append_table(tables)

                    # reset the row count
                    count = 0

                # append header line to last table
                tables[-1]['header'].append(row)

        # loop over tables and append rows
        for table in tables:
            if table['rows']:
                table['columns'] = [{
                    'key': str(idx),
                    'name': 'Column #{}'.format(idx)
                } for idx, value in enumerate(table['rows'][0])]

        return tables

    def append_table(self, tables):
        tables.append({
            'header': [],
            'columns': [],
            'rows': []
        })

    def get_value(self, value):
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            return value

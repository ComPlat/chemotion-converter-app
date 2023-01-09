import logging
import re

from .base import Reader

logger = logging.getLogger(__name__)


class AsciiReader(Reader):
    identifier = 'ascii_reader'
    priority = 1000

    # two or more chars in row
    text_pattern = re.compile(r'[A-Za-z]{2,}')

    def check(self):
        if self.file.encoding == 'binary':
            result = False
        else:
            result = True

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []
        table = self.append_table(tables)

        # loop over lines of the file
        previous_count = None
        for line in self.file.fp.readlines():
            row = line.decode(self.file.encoding).rstrip()
            count = None

            # try to match text for the header
            text_match = self.text_pattern.search(row)
            if text_match:
                if table['rows']:
                    # if a table is already there, this must be a new header
                    table = self.append_table(tables)

                # append header line to last table
                table['header'].append(row)
            else:
                # try to match columns of floats
                row = row.replace('n.a.', '')
                float_match = self.float_pattern.findall(row)
                if float_match:
                    float_match = [self.get_value(float_str) for float_str in float_match]
                    count = len(float_match)

                    if table['rows'] and count != previous_count:
                        # start a new table if the shape has changed
                        self.append_table(tables)

                    table['rows'].append(float_match)

            previous_count = count

        # loop over tables and append columns
        for table in tables:
            if table['rows']:
                table['columns'] = [{
                    'key': str(idx),
                    'name': 'Column #{}'.format(idx)
                } for idx, value in enumerate(table['rows'][0])]

            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))

        return tables

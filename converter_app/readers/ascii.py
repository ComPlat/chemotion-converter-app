import logging
import re
import string

from .base import Reader

logger = logging.getLogger(__name__)

PATTERNS = {
    'text': re.compile(r'[A-Za-z]{2,}'),                 # two or more chars in row
    'floats': re.compile(r'(\d+[,.]*\d*[eE+\-\d]*)\S*')  # e.g. 1.00001E-10
}


class AsciiReader(Reader):
    identifier = 'ascii_reader'

    def check(self):
        file_string, self.encoding = self.peek_ascii()
        result = ('\n' in file_string)

        logger.debug('result=%s', result)
        return result

    def get_data(self):
        tables = []
        self.append_table(tables)

        # a variable to store the current number of columns
        # if this number changes or set to None a new table will be added
        current_length = None

        # loop over lines of the file
        for line in self.file_reader.readlines():
            row = line.decode(self.encoding).rstrip()

            # try to match text for the header
            text_match = PATTERNS['text'].search(row)
            if text_match:
                if current_length is not None:
                    self.append_table(tables)

                # append header line to last table
                tables[-1]['header'].append(row)
                current_length = None

            else:
                # try to match columns of floats
                float_match = PATTERNS['floats'].findall(row)
                if float_match:
                    float_match = [float_str.replace(',', '.')
                                   for float_str in float_match]
                    if current_length == len(float_match):
                        # the current number of columns is the same
                        tables[-1]['rows'].append(float_match)

                    elif current_length is not None:
                        self.append_table(tables)

                    tables[-1]['rows'].append(float_match)
                    current_length = len(float_match)

        # loop over tables and append rows
        for table in tables:
            if table['rows']:
                table['columns'] = [{
                    'key': str(idx),
                    'name': string.ascii_uppercase[idx]
                } for idx, value in enumerate(table['rows'][0])]

        return tables

    def append_table(self, tables):
        tables.append({
            'header': [],
            'columns': [],
            'rows': []
        })

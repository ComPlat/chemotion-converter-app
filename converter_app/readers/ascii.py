import logging
import re

from .base import Reader

logger = logging.getLogger(__name__)

PATTERNS = {
    'text': re.compile(r'[A-Za-z]{2,}'),                   # two or more chars in row
    'floats': re.compile(r'(-?\d+[,.]*\d*[eE+\-\d]*)\S*')  # e.g. 1.00001E-10
}


class AsciiReader(Reader):
    identifier = 'ascii_reader'
    priority = 1000

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        if self.encoding == 'binary':
            result = False
        else:
            result = True

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []
        self.append_table(tables)

        # loop over lines of the file
        previous_count = None
        for line in self.file.readlines():
            row = line.decode(self.encoding).rstrip()
            count = None

            # try to match text for the header
            text_match = PATTERNS['text'].search(row)
            if text_match:
                if tables[-1]['rows']:
                    # if a table is already there, this must be a new header
                    self.append_table(tables)

                # append header line to last table
                tables[-1]['header'].append(row)
            else:
                # try to match columns of floats
                row = row.replace('n.a.','0')
                float_match = PATTERNS['floats'].findall(row)
                if float_match:
                    # replace , by . in floats
                    float_match = [float_str.replace(',', '.') for float_str in float_match]
                    count = len(float_match)

                    if tables[-1]['rows'] and count != previous_count:
                        # start a new table if the shape has changed
                        self.append_table(tables)

                    tables[-1]['rows'].append(float_match)

            previous_count = count

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

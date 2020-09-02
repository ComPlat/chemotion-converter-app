import csv
import io
import re
import logging
import pandas
import string

from .base import Reader

logger = logging.getLogger(__name__)

PATTERNS = {
    'text': re.compile(r'[A-Za-z]{2,}'),                 # two or more chars in row
    'floats': re.compile(r'(\d+[,.]*\d*[eE+\-\d]*)\S*')  # e.g. 1.00001E-10
}


class CSVReader(Reader):
    identifier = 'csv_reader'

    def check(self):
        file_string, self.encoding = self.peek_ascii()

        try:
            self.dialect = csv.Sniffer().sniff(file_string, delimiters=';,\t')
        except csv.Error:
            result = False
        else:
            result = True

        logger.debug('result=%s', result)
        return result

    def get_data(self):
        io_string = io.StringIO(self.file_reader.read().decode(self.encoding))
        reader = csv.reader(io_string, self.dialect)

        try:
            pandas.read_csv(io_string)
            columns = []
            rows = []
            for row in reader:
                if not columns:
                    columns = [{
                        'key': str(idx),
                        'name': string.ascii_uppercase[idx]
                    } for idx, value in enumerate(row)]
                rows.append(row)

            return [{
                'header': [],
                'columns': columns,
                'rows': rows
            }]
        except pandas.errors.ParserError:
            return self.get_data_from_malformed_csv(io_string, reader)

    def get_data_from_malformed_csv(self, io_string, reader):
        io_string.seek(0)
        tables = []
        self.append_table(tables)
        current_length = None

        for row in reader:
            as_string = ' '.join(row)
            text_match = PATTERNS['text'].search(as_string)

            if text_match:
                if current_length is not None:
                    self.append_table(tables)

                # append header line to last table
                tables[-1]['header'].append(as_string)
                current_length = None

            else:
                # try to match columns of floats
                float_match = PATTERNS['floats'].findall(as_string)
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

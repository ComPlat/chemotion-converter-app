import copy
import csv
import io
import logging

from .base import Reader

logger = logging.getLogger(__name__)


class CSVReader(Reader):
    identifier = 'csv_reader'
    priority = 100

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        if self.encoding == 'binary':
            result = False
        else:
            file_string = self.file_content.decode(self.encoding)

            try:
                dialect = csv.Sniffer().sniff(file_string, delimiters=';,\t')
            except csv.Error:
                result = False
            else:
                io_string = io.StringIO(file_string)
                self.lines = copy.copy(io_string)
                self.reader = csv.reader(io_string, dialect)
                result = True

        logger.debug('result=%s', result)
        return result

    def get_data(self):
        tables = []
        self.append_table(tables)

        previous_shape = []
        previous_row = []
        for line, row in zip(self.lines, self.reader):
            shape = self.get_shape(row)

            if 'f' in shape and shape == previous_shape:
                if tables[-1]['rows'] == []:
                    # move the previous row with the same shape from the header to the table
                    tables[-1]['header'].pop()
                    tables[-1]['rows'].append(previous_row)

                tables[-1]['rows'].append(row)

            else:
                if tables[-1]['rows']:
                    # start a new table if the shape has changed
                    self.append_table(tables)

                tables[-1]['header'].append(line)

            # store shape and row for the next iteration
            previous_shape = shape
            previous_row = row

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

    def get_shape(self, row):
        shape = []
        for cell in row:
            if cell.strip() == '':
                shape.append('')
            else:
                try:
                    float(cell.replace(',', '.'))
                    shape.append('f')
                except ValueError:
                    shape.append('s')
        return shape

import copy
import csv
import io
import logging
import string

from .base import Reader

logger = logging.getLogger(__name__)


class CSVReader(Reader):
    identifier = 'csv_reader'
    priority = 100

    def check(self):
        file_string, encoding = self.peek_ascii()

        try:
            dialect = csv.Sniffer().sniff(file_string, delimiters=';,\t')
        except csv.Error:
            result = False
        else:
            io_string = io.StringIO(self.file.read().decode(encoding))
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

            if 's' in shape:
                # there is a string in this row, this cant be the table

                if tables[-1]['rows']:
                    # if a table is already there, this must be a new header
                    self.append_table(tables)

                tables[-1]['header'].append(line)

            elif 'f' in shape:
                if tables[-1]['rows'] and shape != previous_shape:
                    # start a new table if the shape has changed
                    self.append_table(tables)

                elif tables[-1]['rows'] == [] and [bool(s) for s in shape] == [bool(s) for s in previous_shape]:
                    # move the previous row with a "similar" shape from the header to the table
                    tables[-1]['header'].pop()
                    values = [previous_row[i] for i, value in enumerate(previous_shape) if value != '']
                    tables[-1]['rows'].append(values)

                # this row has floats but no strings, this is the "real" table
                values = [row[i] for i, value in enumerate(shape) if value == 'f']
                tables[-1]['rows'].append(values)

            else:
                # empty lines are preserved for the header
                tables[-1]['header'].append(line)

            # store shape and row for the next iteration
            previous_shape = shape
            previous_row = row

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

import logging
import string
import zipfile

import openpyxl

from .base import Reader

logger = logging.getLogger(__name__)


class ExcelReader(Reader):
    identifier = 'excel_reader'
    priority = 10

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        if self.encoding != 'binary':
            result = False
        else:
            try:
                self.wb = openpyxl.load_workbook(filename=self.file)
                result = True
            except (openpyxl.utils.exceptions.InvalidFileException, zipfile.BadZipFile):
                result = False

        logger.debug('result=%s', result)
        return result

    def get_data(self):
        tables = []

        # loop over worksheets
        for ws in self.wb:
            self.append_table(tables)

            previous_shape = None
            previous_row = None
            for row in ws.values:
                shape = self.get_shape(row)

                if 's' in shape:
                    # there is a string in this row, this cant be the table

                    if tables[-1]['rows']:
                        # if a table is already there, this must be a new header
                        self.append_table(tables)

                    tables[-1]['header'].append('\t'.join([str(cell) for cell in row]))

                elif 'f' in shape:
                    if tables[-1]['rows'] and shape != previous_shape:
                        # start a new table if the shape has changed
                        self.append_table(tables)

                    elif tables[-1]['rows'] == [] and [bool(s) for s in shape] == [bool(s) for s in previous_shape]:
                        # move the previous row with a "similar" shape from the header to the table
                        tables[-1]['header'].pop()
                        values = [previous_row[i] for i, value in enumerate(previous_shape) if value is not None]
                        tables[-1]['rows'].append(values)

                    # this row has floats but no strings, this is the "real" table
                    values = [row[i] for i, value in enumerate(shape) if value == 'f']
                    tables[-1]['rows'].append(values)

                else:
                    # empty lines are preserved for the header
                    tables[-1]['header'].append(row)

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
            if cell is None:
                shape.append(None)
            else:
                try:
                    float(cell)
                    shape.append('f')
                except (ValueError, TypeError):
                    shape.append('s')
        return shape

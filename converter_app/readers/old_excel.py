import logging
import xlrd

from converter_app.readers.helper import get_shape
from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)


class OldExcelReader(Reader):
    """
    Reads old .xls files
    """
    identifier = 'old_excel_reader'
    priority = 16

    def __init__(self, file):
        super().__init__(file)
        self.wb = None

    def check(self):
        if self.file.encoding != 'binary' or self.file.suffix != '.xls':
            return False
        try:
            self.wb = xlrd.open_workbook(file_contents=self.file.content)
            return True
        except:
            return False

    def _add_unique_key(self, key, value):
        o_key = key
        idx = 1
        while key in self.tables[-1]['metadata']:
            key = f"{o_key} ({idx})"
            idx += 1
        self.tables[-1]['metadata'][key] = value

    def prepare_tables(self):
        self.tables = []

        # loop over worksheets
        for ws in self.wb:
            self.append_table(self.tables)

            previous_shape = None
            for row in ws:

                row = self._parse_row(row)
                shape = get_shape(row)

                if 's' in shape:
                    # there is a string in this row, this cant be the table

                    if self.tables[-1]['rows']:
                        # if a table is already there, this must be a new header
                        self.append_table(self.tables)

                    self.tables[-1]['header'].append('\t'.join([str(cell) for cell in row]))
                    for val in row[1:]:
                        self._add_unique_key(row[0], val)

                elif 'f' in shape:
                    if self.tables[-1]['rows'] and shape != previous_shape:
                        # start a new table if the shape has changed
                        self.append_table(self.tables)

                    # this row has floats but no strings, this is the "real" table
                    values = [row[i] for i, value in enumerate(shape) if value == 'f']
                    self.tables[-1]['rows'].append(values)

                else:
                    # empty lines are preserved for the header
                    self.tables[-1]['header'].append(row)

                # store shape and row for the next iteration
                previous_shape = shape

        return self.tables

    def _parse_row(self, row):
        return [cell.value for cell in row]


Readers.instance().register(OldExcelReader)

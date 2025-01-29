import logging
import zipfile

import openpyxl

from converter_app.readers.helper.base import Reader, Table
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class ExcelReader(Reader):
    """
    Reads and converts Excel Files
    """
    identifier = 'excel_reader'
    priority = 15

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self.wb = None
        self._table_row_meta = Table()
        self._table_col_meta = Table()

    def check(self):
        """
        :return: True if it fits
        """
        if self.file.encoding != 'binary':
            result = False
        elif self.file.suffix != '.xlsx':
            result = False
        else:
            try:
                self.wb = openpyxl.load_workbook(filename=self.file.fp)
                result = True
            except (openpyxl.utils.exceptions.InvalidFileException, zipfile.BadZipFile):
                result = False

        logger.debug('result=%s', result)
        return result

    def prepare_tables(self):
        tables = []
        # A, B, C
        # C , C ,C ,C
        # loop over worksheets
        for ws in self.wb:
            self.append_table(tables)
            keys = []

            previous_shape = None
            for row in ws.values:
                shape = self.get_shape(row)

                if 's' in shape:
                    # there is a string in this row, this cant be the table
                    self._set_col_metadata(row)
                    if tables[-1]['rows']:
                        # if a table is already there, this must be a new header
                        self.append_table(tables)
                        keys = []

                    tables[-1]['header'].append('\t'.join([str(cell) for cell in row]))
                    self._set_row_metadata(keys, row, True)

                elif 'f' in shape:
                    if tables[-1]['rows'] and shape != previous_shape:
                        # start a new table if the shape has changed
                        self.append_table(tables)
                        keys = []
                    else:
                        self._set_row_metadata(keys, row, False)
                    # this row has floats but no strings, this is the "real" table
                    values = [row[i] for i, value in enumerate(shape) if value == 'f']
                    tables[-1]['rows'].append(values)

                else:
                    # empty lines are preserved for the header
                    tables[-1]['header'].append(', '.join([str(x) for x in row]))

                # store shape and row for the next iteration
                previous_shape = shape
        tables.append(self._table_row_meta)
        tables.append(self._table_col_meta)
        return tables

    def _set_row_metadata(self, keys, row, set_keys):
        """Sets the metadata for the table."""
        if len(keys) == 0:
            if set_keys:
                for cell in row:
                    keys.append(str(cell))
        else:
            for cell in row:
                key = keys.pop(0)
                if set_keys:
                    keys.append(str(cell))
                if key != 'None':
                    self._table_row_meta['metadata'].add_unique(key, str(cell))

    def _set_col_metadata(self, row):
        row = [x for x in row if x != 'None']
        shape = self.get_shape(row)
        if len(shape) < 4 and shape[0] == 's':
            for val in row[1:]:
                self._table_col_meta['metadata'].add_unique(row[0], str(val))

Readers.instance().register(ExcelReader)

import logging
import zipfile

import openpyxl

from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader

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

        # loop over worksheets
        for ws in self.wb:
            self.append_table(tables)

            previous_shape = None
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

                    # this row has floats but no strings, this is the "real" table
                    values = [row[i] for i, value in enumerate(shape) if value == 'f']
                    tables[-1]['rows'].append(values)

                else:
                    # empty lines are preserved for the header
                    tables[-1]['header'].append(', '.join([str(x) for x in row]))

                # store shape and row for the next iteration
                previous_shape = shape

        return tables

Readers.instance().register(ExcelReader)

import csv
import io
import logging
from enum import Enum

from .base import Reader

logger = logging.getLogger(__name__)

class MODES(Enum):
    START = 0
    END = -1
    META = 1
    TABLE_X = 2
    TABLE_Y = 3
    END_TABLE = 4
class AeCmsReader(Reader):
    identifier = 'ae-cms-reader'
    priority = 10
    delimiters = {
        ',': 'comma',
    }

    def __init__(self, file):
        super().__init__(file)
        self._row_length = 0
        self._key_chain = ['']*10

    def check(self):
        # check using seperate function for inheritance
        result = self.file.suffix.lower() == '.csv' and self.file.mime_type == 'text/plain'
        if result:
            self.lines = self.file.string.splitlines()
            result = 'Advion ExpressIon CMS' in self.lines[0]

        logger.debug('result=%s', result)
        return result


    def _get_next_mode(self, row, mode):
        if row[0] == 'Retention Time\\Intensities\\Masses':
            try:
                row = [float(x) for x in row[1:]]
                self._row_length = len(row)
                return (row, MODES.TABLE_X)
            except:
                mode = MODES.META

        if mode == MODES.END_TABLE or mode == MODES.START:
            mode = MODES.META

        if mode == MODES.TABLE_X:
            mode = MODES.TABLE_Y

        if mode == MODES.TABLE_Y:

            try:
                row = [float(x) for x in row[1:] if x != '']
                if len(row) >= self._row_length:
                    return (row, mode)
            except:
                pass
            mode = MODES.END_TABLE
        if mode == MODES.END or len(row) > 1 and row[0] == 'Start (m/z)':
            return ([], MODES.END)
        if mode == MODES.META:
            if len(row) < 2:
                return ([], mode)
            key = []
            for (idx, key_elm) in enumerate(row[:-1]):
                if key_elm != '':
                    key.append(key_elm)
                    self._key_chain[idx] = key_elm
                else:
                    key.append(self._key_chain[idx])
            row = ['.'.join(key), row[-1]]

        return (row, mode)

    def get_tables(self):
        tables = []
        table = self.append_table(tables)
        mode = MODES.START
        y_vals = []
        x_vals = []
        # loop over lines of the file
        previous_count = None
        for line in self.lines:
            row = [x.strip() for x in line.split(',')]
            (row, mode) = self._get_next_mode(row, mode)
            if mode == MODES.START or mode ==MODES.END:
                table['header'].append(line)
            elif mode == MODES.META:
                table['header'].append(line)
                if len(row) == 2:
                    table['metadata'][row[0]] = row[1]
            elif mode == MODES.TABLE_X:
                x_vals = row
                y_vals = [0] * len(row)
            elif mode == MODES.TABLE_Y:
                for (idx, vla) in enumerate(y_vals):
                    y_vals[idx] = max(vla, row[idx])
            elif mode == MODES.END_TABLE:
                for i in range(self._row_length):
                    table['rows'].append([x_vals[i], y_vals[i]])
                y_vals = x_vals = None


        # loop over tables and append columns
        for table in tables:
            if table['rows']:
                table['columns'] = [{
                    'key': str(idx),
                    'name': 'Column #{}'.format(idx)
                } for idx, value in enumerate(['Mass (m/z)', 'Max. intensity'])]

            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))
            table['metadata']['Column #0'] = 'Mass (m/z)'
            table['metadata']['Column #1'] = 'Max. intensity'

        return tables
import copy
import csv
import io
import logging
import re
import sys
from converter_app.readers.helper.reader import Readers
from .csv_reader import CSVReader

logger = logging.getLogger(__name__)

unit_pattern = re.compile(r'\(([a-zA-Z])\)$')


class NovaReader(CSVReader):
    """
    Nova reader reads special csv Files
    """
    identifier = 'nova_reader'
    priority = 90

    first_row = ['Potential applied (V)', 'Time (s)', 'WE(1).Current (A)', 'WE(1).Potential (V)', 'Scan', 'Index', 'Q+',
                 'Q-']
    scan_index = 4

    def __init__(self, file):
        super().__init__(file)
        self._step_size_unit = None
        self._scan_rate_unit = None
        self._total_rows = 0
        self._cycles = 0

    def check(self):
        # check using separate function in the CSVReader
        result = self.check_csv()
        if result:
            first_line = self.file.string.splitlines()[0]
            first_row = next(csv.reader(io.StringIO(first_line), self.file.features('csv_dialect')))
            if first_row[:8] == self.first_row:
                self.rows = list(csv.reader(io.StringIO(self.file.string), self.file.features('csv_dialect')))
                self.lines = self.file.string.splitlines()
            else:
                result = False

        logger.debug('result=%s', result)
        return result

    def prepare_tables(self):
        tables = []
        table = None
        scan = None
        prev = None

        for csv_table in super().prepare_tables():
            for row in csv_table['rows']:
                if row[self.scan_index] != scan:
                    scan = row[self.scan_index]
                    table = {
                        'header': [],
                        'metadata': copy.deepcopy(csv_table.get('metadata', {})),
                        'columns': copy.deepcopy(csv_table.get('columns', [])),
                        'rows': []
                    }

                    # add the units of some of the colums as metadata
                    for key in list(table['metadata'].keys()):
                        if key.startswith('column_'):
                            match = unit_pattern.search(table['metadata'][key])
                            if match:
                                table['metadata'][key + '_unit'] = match.group(1)

                    # add additional columns
                    if self._step_size_unit is None and 'column_00_unit' in table['metadata']:
                        self._step_size_unit = f'{table["metadata"]["column_00_unit"]}'

                    if self._scan_rate_unit is None and 'column_00_unit' in table['metadata'] and 'column_01_unit' in \
                            table['metadata']:
                        self._scan_rate_unit = f'{table["metadata"]["column_00_unit"]}/{table["metadata"]["column_01_unit"]}'

                    for column in [
                        ('Step size', self._step_size_unit),
                        ('Scan rate', self._scan_rate_unit)
                    ]:
                        idx = len(table['columns'])
                        name, unit = column
                        table['columns'].append({
                            'key': str(idx),
                            'name': f'Column #{idx} ({name} ({unit}))'
                        })
                        table['metadata'][f'column_{idx:02d}'] = f'{name} ({unit})' if unit else name
                        table['metadata'][f'column_{idx:02d}_unit'] = unit

                    self._cycles = max(int(scan), self._cycles)

                    table['metadata']['scan'] = scan
                    tables.append(table)

                # compute additional columns
                if prev is None:
                    table['rows'].append(row + ['nan', 'nan'])
                else:
                    step_size = float(row[0]) - float(prev[0])
                    scan_rate = step_size / (float(row[1]) - float(prev[1]))
                    table['rows'].append(row + [str(step_size), str(scan_rate)])

                prev = row

        for table in tables:
            self._total_rows += len(table['rows'])

        return tables

    def get_metadata(self):
        v_init = self.tables[0]['rows'][0][0]
        v_end = self.tables[-1]['rows'][-1][0]

        idx = 0
        v_max, v_max_idx = sys.float_info.min, 0
        v_min, v_min_idx = sys.float_info.max, 0
        for table in self.tables:
            for row in table['rows']:
                value = float(row[0])
                if value > v_max:
                    v_max, v_max_idx = value, idx
                if value < v_min:
                    v_min, v_min_idx = value, idx
                idx += 1

        if v_max_idx < v_min_idx:
            v_limit1, v_limit2 = v_max, v_min
        else:
            v_limit1, v_limit2 = v_min, v_max

        step_size = sum(
            sum(abs(float(row[-2])) for row in table['rows'][1:]) for table in self.tables) / self._total_rows
        scan_rate = sum(
            sum(abs(float(row[-1])) for row in table['rows'][1:]) for table in self.tables) / self._total_rows

        metadata = super().get_metadata()
        metadata.update({
            'v_init': str(v_init),
            'v_end': str(v_end),
            'v_max': str(v_max),
            'v_min': str(v_min),
            'v_limit1': str(v_limit1),
            'v_limit2': str(v_limit2),
            'step_size': str(step_size),
            'step_size_unit': self._step_size_unit,
            'scan_rate': str(scan_rate),
            'scan_rate_unit': self._scan_rate_unit,
            'cycles': str(self._cycles)
        })

        return metadata


Readers.instance().register(NovaReader)

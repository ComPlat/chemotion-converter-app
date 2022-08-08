import copy
import csv
import io
import logging
import re

from .csv import CSVReader

logger = logging.getLogger(__name__)

unit_pattern = re.compile(r'\(([a-zA-Z])\)$')


class NovaReader(CSVReader):
    identifier = 'nova_reader'
    priority = 90

    first_row = ['Potential applied (V)', 'Time (s)', 'WE(1).Current (A)', 'WE(1).Potential (V)', 'Scan', 'Index', 'Q+', 'Q-']
    scan_index = 4

    def check(self):
        # check using seperate function in the CSVReader
        result = self.check_csv()
        if result:
            first_line = self.file.string.splitlines()[0]
            first_row = next(csv.reader(io.StringIO(first_line), self.file.csv_dialect))
            if first_row[:8] == self.first_row:
                self.rows = list(csv.reader(io.StringIO(self.file.string), self.file.csv_dialect))
                self.lines = self.file.string.splitlines()
            else:
                result = False

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []
        table = None
        scan = None
        prev = None

        self.step_size_unit = None
        self.scan_rate_unit = None

        for csv_table in super().get_tables():
            for row in csv_table['rows']:
                if row[self.scan_index] != scan:
                    scan = row[self.scan_index]
                    table = {
                        'header': [],
                        'metadata': copy.deepcopy(csv_table.get('metadata', {})),
                        'columns': copy.deepcopy(csv_table.get('columns', {})),
                        'rows': []
                    }

                    # add the units of some of the colums as metadata
                    for key in list(table['metadata'].keys()):
                        if key.startswith('column_'):
                            match = unit_pattern.search(table['metadata'][key])
                            if match:
                                table['metadata'][key + '_unit'] = match.group(1)

                    # add additional columns
                    if self.step_size_unit is None and 'column_00_unit' in table['metadata']:
                        self.step_size_unit = '{column_00_unit}'.format(**table['metadata'])

                    if self.scan_rate_unit is None and 'column_00_unit' in table['metadata'] and 'column_01_unit' in table['metadata']:
                        self.scan_rate_unit = '{column_00_unit}/{column_01_unit}'.format(**table['metadata'])

                    for i, column in enumerate([
                        ('Step size', self.step_size_unit),
                        ('Scan rate', self.scan_rate_unit)
                    ]):
                        idx = len(table['columns']) + i
                        name, unit = column
                        table['columns'].append({
                            'key': str(idx),
                            'name': 'Column #{} ({} ({}))'.format(idx, name, unit)
                        })
                        table['metadata']['column_{:02d}'.format(idx)] = '{} ({})'.format(name, unit) if unit else name
                        table['metadata']['column_{:02d}_unit'.format(idx)] = unit

                    table['metadata']['scan'] = int(scan)
                    tables.append(table)

                # compute additional columns
                if prev is None:
                    table['rows'].append(row + ['nan', 'nan'])
                else:
                    delta_v = float(row[0]) - float(prev[0])
                    v_s = delta_v / (float(row[1]) - float(prev[1]))
                    table['rows'].append(row + [str(delta_v), str(v_s)])

                prev = row

        for table in tables:
            table['metadata']['rows'] = len(table['rows'])
            table['metadata']['columns'] = len(table['columns'])

        return tables

    def get_metadata(self):
        total_rows = sum([table['metadata']['rows'] for table in self.tables])

        v_init = self.tables[0]['rows'][0][0]
        v_end = self.tables[-1]['rows'][-1][0]
        v_max = max([max([float(row[0]) for row in table['rows']]) for table in self.tables])
        v_min = min([min([float(row[0]) for row in table['rows']]) for table in self.tables])
        step_size = sum([sum([abs(float(row[-2])) for row in table['rows'][1:]]) for table in self.tables]) / total_rows
        scan_rate = sum([sum([abs(float(row[-1])) for row in table['rows'][1:]]) for table in self.tables]) / total_rows
        cycles = max([table['metadata']['scan'] for table in self.tables])

        metadata = super().get_metadata()
        metadata.update({
            'v_init': v_init,
            'v_end': v_end,
            'v_max': v_max,
            'v_min': v_min,
            'step_size': step_size,
            'step_size_unit': self.step_size_unit,
            'scan_rate': scan_rate,
            'scan_rate_unit': self.scan_rate_unit,
            'cycles': cycles
        })
        return metadata

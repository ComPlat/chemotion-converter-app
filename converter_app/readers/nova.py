import copy
import csv
import io
import logging

from .csv import CSVReader

logger = logging.getLogger(__name__)


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
                    table['metadata']['scan'] = int(scan)
                    tables.append(table)

                table['rows'].append(row)

        for table in tables:
            table['metadata']['rows'] = len(table['rows'])
            table['metadata']['columns'] = len(table['columns'])

        return tables

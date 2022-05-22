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
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        # check using seperate function in the CSVReader
        result, file_string = self.check_csv()
        if result:
            first_line = file_string.splitlines()[0]
            first_row = next(csv.reader(io.StringIO(first_line), self.dialect))
            if first_row[:8] == self.first_row:
                self.rows = list(csv.reader(io.StringIO(file_string), self.dialect))
                self.lines = file_string.splitlines()
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

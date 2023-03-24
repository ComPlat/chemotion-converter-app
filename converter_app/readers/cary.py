import csv
import io
import logging
import re
import os

from .csv import CSVReader

logger = logging.getLogger(__name__)


class CaryReader(CSVReader):
    identifier = 'cary_reader'
    priority = 90

    metadata_patterns = {
        'Collection Time': re.compile(r'Collection Time\s*:\s*(.*)'),
        'Operator Name': re.compile(r'Operator Name\s*:\s*(.*)'),
        'Scan Version': re.compile(r'Scan Version\s*(.*)'),
        'Parameter List': re.compile(r'Parameter List\s*:\s*(.*)'),
        'Instrument': re.compile(r'Instrument \s*((?!Version).*)'),
        'Instrument Version': re.compile(r'Instrument Version\s*(.*)'),
        'Start (nm)': re.compile(r'Start \(nm\)\s*(.*)'),
        'Stop (nm)': re.compile(r'Stop \(nm\)\s*(.*)'),
        'X Mode': re.compile(r'X Mode\s*(.*)'),
    }

    # Collection Time: 6/17/2021 4:53:42 PM
    # Operator Name  :
    # Scan Version 5.1.0.1016
    # Parameter List :
    # Instrument  Cary 60
    # Instrument Version  2.00
    # Start (nm)  1000.0
    # Stop (nm)  200.0
    # X Mode  Nanometers

    def check(self):
        # check using seperate function in the CSVReader
        result = self.check_csv()
        if result:
            # split the file at the first empty line
            split = re.split(r'(?:\r?\n){2,}', self.file.string.strip())

            try:
                data_string, metadata_string = split
            except ValueError:
                result = False

            if result and 'Instrument  Cary' in metadata_string:
                self.rows = list(csv.reader(io.StringIO(data_string), self.file.csv_dialect))
                self.lines = data_string.splitlines()
                self.metadata_lines = metadata_string.splitlines()
            else:
                result = False

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = super().get_tables()

        # loop over the metadata lines and try to find the metadata patterns
        metadata = {}
        for line in self.metadata_lines:
            for key, pattern in self.metadata_patterns.items():
                match = pattern.search(line)
                if match:
                    metadata[key] = match.group(1)

        # add the metadata lines to the table header and the metadata to the table metadata
        tables[0]['header'] += [os.linesep] + self.metadata_lines
        tables[0]['metadata'].update(metadata)
        print(metadata)
        return tables

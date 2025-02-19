import logging
import re

from converter_app.models import File
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class UXDReader(Reader):
    """
    Reader for UDX files. Files from: Powder Diffraction -  Diffrac Plus

    Test File: test_files/data_files/Powder Diffraction/Diffrac Plus/XCH-UXD/PD-01-02(2).UXD
    """

    identifier = 'uxd_reader'
    priority = 10

    def __init__(self, file: File, *tar_content):
        super().__init__(file, *tar_content)
        self._step_size = None
        self._start = None
        self._file_extensions = ['.uxd']
        self._table = None
        self._version = 2
        self._max_table_length = 0

    def check(self):
        return self.file.suffix.lower() in self._file_extensions

    def _read_data(self, data_rows: list[str]):
        if '_COUNTS' in self._table['header'][-2:]:
            for line in data_rows:
                try:
                    new_row = [self.as_number(x.strip()) for x in line.split(' ') if x != '']
                    if len(new_row) > 0:
                        self._max_table_length = 1
                        for val in new_row:
                            self._table['rows'].append([self._start + self._step_size * len(self._table['rows']), val])
                except ValueError:
                    pass
        else:
            for line in data_rows:
                try:
                    line = line.strip()
                    if line != '':
                        value = [self.as_number(x) for x in re.split(r'[\t\s]+', line) if x != '']
                        self._table['rows'].append([value[0], value[1]])
                except (ValueError, IndexError):
                    pass

    def _add_metadata(self, key, val):
        if self.float_pattern.fullmatch(val):
            val = self.get_value(val)
        self._table.add_metadata(key, val)

    def prepare_tables(self):
        tables = []
        self._table = self.append_table(tables)
        data_rows = []
        for row in self.file.fp.readlines():
            line = row.decode(self.file.encoding).rstrip()

            if len(line) > 1 and (line[0] == '_' or line[0] == ';'):
                self._table['header'].append(line)
                if line[0] == '_' and line[1] != '+' and '=' in line:
                    data = line.split('=')
                    key = data[0].strip()[1:]
                    value = data[1].strip().replace('\n', '')
                    self._add_metadata(key, value)
            else:
                data_rows.append(line)
        try:
            self._version = int(self._table['metadata'].get('FILEVERSION'))
        except ValueError:
            self._version = 0

        if 'START' in self._table['metadata'] and 'STEPSIZE' in self._table['metadata']:
            self._step_size = self.as_number(self._table['metadata']['STEPSIZE'])
            self._start = self.as_number(self._table['metadata']['START'])
        else:
            self._step_size = self._start = 0

        self._read_data(data_rows)

        self._table.add_metadata("END", self._table['rows'][-1][0])




        return tables


Readers.instance().register(UXDReader)

import logging

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
        self._file_extensions = ['.uxd']
        self._table = None
        self._version = 2
        self._max_table_length = 0

    def check(self):
        return self.file.suffix.lower() in self._file_extensions

    def _read_data(self, line: str):
        if self._version == 2:
            try:
                new_row = [self.as_number(x.strip()) for x in line.split(' ') if x != '']
                if len(new_row) > 0:
                    self._max_table_length = max(self._max_table_length, len(new_row))
                    self._table['rows'].append(new_row)
            except ValueError:
                pass
        elif self._version == 3:
            try:
                value = [self.as_number(x.strip()) for x in line.split('\t')]
                self._table['rows'].append([value[0], value[1]])
            except ValueError:
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

        for row in data_rows:
            self._read_data(row)

        for row in self._table['rows']:
            while len(row) < self._max_table_length:
                row.append('')

        if 'START' in self._table['metadata'] and 'STEPSIZE' in self._table['metadata']:
            end = self.as_number(self._table['metadata']['START']) + (
                        self.as_number(self._table['metadata']['STEPSIZE']) * (len(self._table['rows']) - 1))
            self._table.add_metadata("END", end)

        return tables


Readers.instance().register(UXDReader)

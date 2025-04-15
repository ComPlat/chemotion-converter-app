import re

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers


class MpsReader(Reader):
    """
    Implementation of the MPS Reader. It extends converter_app.readers.helper.base.Reader
    Also reads MPL Files.
    """
    identifier = 'mps_reader'
    priority = 10
    prev_key = ''
    values = ''

    def check(self):
        """
        :return: True if it fits
        """
        return self.file.suffix in ('.mps', '.mpl')

    def prepare_tables(self):
        tables = []
        header = False
        multiline = False
        key = ''
        new_table = False
        table = self.append_table(tables)

        for line in self.file.fp.readlines():
            row = line.decode(self.file.encoding).rstrip()
            if len(row) == 0:
                continue

            if new_table:
                table = self.append_table(tables)
                table['header'].append('Technique : ' + MpsReader.values)
                MpsReader.prev_key = ''
                MpsReader.values = ''
                new_table = False

            if re.search(r'^\t.*', row):
                multiline = True
            elif not re.search(r'[:=]', row) and not re.search(r'\s{2,}', row):
                header = True

            if not multiline:
                MpsReader.prev_key = ''
                MpsReader.values = ''

            if header:
                self._handle_header(row, table)
                header = False
            elif multiline:
                self._handle_multiline(key, row, table)
                multiline = False
            else:
                if re.search(r'\s{2,}', row):
                    self._handle_sub_table(row, table)
                elif ':' in row:
                    key, new_table = self._handle_colon(key, row, table)
                else:
                    self._handle_equation_list(row, table)

        MpsReader.prev_key = ''
        MpsReader.values = ''
        return tables

    @staticmethod
    def _handle_header(row, table):
        if re.search(r'^Record', row):
            if 'Record' in table['metadata']:
                table['metadata']['Record'] += ', ' + row[7:]
            else:
                table['metadata']['Record'] = row[7:]
        else:
            table['header'].append(row)

    @staticmethod
    def _handle_colon(key, row, table):
        """
         handles metadata e.g. x: 5
         and detects multiline attempts
        """
        k_v = [x.strip() for x in row.split(':', 1)]
        if k_v[0] == 'Technique':
            MpsReader.values = k_v[1]
            return key, True
        if k_v[1] == '':
            key = k_v[0]
        else:
            table['metadata'][k_v[0]] = k_v[1]
        return key, False

    @staticmethod
    def _handle_sub_table(row, table):
        k_v = re.split(r'\s{2,}', row)
        value = k_v[1]
        for v in k_v[2:]:
            value += ',' + v
        table['metadata'][k_v[0]] = '[' + value + ']'

    @staticmethod
    def _handle_multiline(key, row, table):
        if key != '':
            if ':' in row:
                k_v = [x.strip() for x in row.lstrip().split(':', 1)]
                table['metadata'][key + '.' + k_v[0]] = k_v[1]
            else:
                if MpsReader.prev_key != key:
                    MpsReader.values = ''
                    MpsReader.prev_key = key
                    MpsReader.values = row.lstrip()
                else:
                    MpsReader.values += ', ' + row.lstrip()

                table['metadata'][key] = MpsReader.values
        else:
            table['header'].append(row)  # Header with leading tab or missing ':' in previous line

    @staticmethod
    def _handle_equation_list(eql, table):
        eqs = [x.strip() for x in eql.split(',', 1)]
        for eq in eqs:
            k_v = [x.strip() for x in eq.split('=', 1)]
            table['metadata'][k_v[0]] = k_v[1]


Readers.instance().register(MpsReader)

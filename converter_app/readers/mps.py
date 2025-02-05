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
                new_table = False

            if re.search(r'^\t.*', row):
                multiline = True
            elif not re.search(r'[:=]', row) and not re.search(r'\s{2,}', row):
                header = True

            if header:
                table['header'].append(row)
                header = False
            elif multiline:
                self.handle_multiline(key, row, table)
                multiline = False
            else:
                if re.search(r'\s{2,}', row):
                    self.handle_sub_table(row, table)
                elif ':' in row:
                    key, new_table = self.handle_colon(key, row, table)
                else:
                    self.handle_equation_list(row, table)
        return tables

    @staticmethod
    def handle_colon(key, row, table):
        """
         handles metadata e.g. x: 5
         and detects multiline attempts
        """
        k_v = [x.strip() for x in row.split(':', 1)]
        if k_v[0] == 'Technique':
            return key, True
        if k_v[1] == '':
            key = k_v[0]
        else:
            table['metadata'].add_unique(k_v[0], k_v[1])
        return key, False

    @staticmethod
    def handle_sub_table(row, table):
        """
         handles tables separated by multiple spaces
        """
        k_v = re.split(r'\s{2,}', row)
        value = k_v[1]
        for v in k_v[2:]:
            value += ',' + v
        table['metadata'].add_unique(k_v[0], '[' + value + ']')

    @staticmethod
    def handle_multiline(key, row, table):
        """
         handles multiline metadata e.g. x:
            5
        """
        if key != '':
            if ':' in row:
                k_v = [x.strip() for x in row.lstrip().split(':', 1)]
                table['metadata'].add_unique(key + '.' + k_v[0], k_v[1])
            else:
                table['metadata'].add_unique(key, row.lstrip())
        else:
            table['header'].append(row)  # Header with leading tab or missing ':' in previous line

    @staticmethod
    def handle_equation_list(eql, table):
        """
         handles list of equations, e.q. a=5,b=3,c=8
        """
        eqs = [x.strip() for x in eql.split(',', 1)]
        for eq in eqs:
            k_v = [x.strip() for x in eq.split('=', 1)]
            table['metadata'].add_unique(k_v[0], k_v[1])


Readers.instance().register(MpsReader)

import io
import os
import sys
from collections import defaultdict
from typing import Any, Generator

from .base import Writer
from .. import TITLE, VERSION
from ..options import DATA_TYPES, DATA_CLASSES, XUNITS, YUNITS


class JcampWriter(Writer):

    nline = 12
    suffix = '.jdx'
    mimetype = 'chemical/x-jcamp-dx'

    def __init__(self, converter):
        super().__init__(converter)
        self.buffer: io.StringIO | None = None

    def process(self):
        self.process_table(self.tables[0])

    def process_ntuples_tables(self) -> Generator[list, Any, None]:
        """
        Prepares single jdx for all NTUPLES data tables
        """
        ntuples_tables = [table for table in self.tables if table.get('header', {}).get('DATA CLASS') == 'NTUPLES']

        # 1. Group the objects using a defaultdict
        grouped_tables = defaultdict(list)

        for table in ntuples_tables:
            # Use the 'header' attribute as the key to group by
            grouped_tables[table['header']['NTUPLES_ID']].append(table)

        for tables in grouped_tables.values():
            self.buffer = io.StringIO()
            header = tables[0].get('header', {})
            self._prepare_main_header(header)
            self._process_ntuples(header, tables)
            yield tables

    def process_table(self, table):
        """
        Prepares single jdx for one file
        :param table: Converted table to be processed
        """
        self.buffer = io.StringIO()
        header = table.get('header', {})

        self._prepare_main_header(header)

        if not table.get('y') or not table.get('x'):
            return
        self._prepare_calculation_header(table)

        data_class = header.get('DATA CLASS', DATA_CLASSES[0])
        if data_class == 'XYDATA':
            self._process_xydata(header, table.get('y'))
        elif data_class in ['XYPOINTS', 'PEAK TABLE']:
            self._process_xypoints(header, table.get('x'), table.get('y'))
        elif data_class == 'NTUPLES':
            self._process_ntuples(header, [table])

    def _prepare_main_header(self, header):
        jcamp_header = {
            'TITLE': header.get('TITLE', 'Spectrum'),
            'JCAMP-DX': f'5.00 $$ {TITLE} ({VERSION})',
            'DATA TYPE': header.get('DATA TYPE', DATA_TYPES[0]),
            'DATA CLASS': header.get('DATA CLASS', DATA_CLASSES[0]),
            'ORIGIN': header.get('ORIGIN', ''),
            'OWNER': header.get('OWNER', '')
        }
        black_list = ['NTUPLES_PAGE_HEADER_VALUE']
        for key in header:
            key_upper = key.upper()
            if key_upper not in black_list and key_upper not in jcamp_header:
                jcamp_header[key_upper] = header[key]
        self._write_header(jcamp_header)

    def _prepare_calculation_header(self, table, add_comment = True):
        jcamp_header = {}
        if table.get('applied_x_operator'):
            jcamp_header['CALCULATION_APPLIED_X'] = True
            if add_comment and table.get('x_operations_description'):
                self.write_comment_header(
                    ['X operations description:'] + table.get('x_operations_description'))

        if table.get('applied_y_operator'):
            jcamp_header['CALCULATION_APPLIED_Y'] = True
            if add_comment and table.get('y_operations_description'):
                self.write_comment_header(
                    ['Y operations description:'] + table.get('y_operations_description'))

        if table.get('applied_operator_failed'):
            jcamp_header['CALCULATION_FAILED'] = True
        self._write_header(jcamp_header)

    def _process_xydata(self, header, y):
        firstx = header.get('FIRSTX')
        lastx = header.get('LASTX')
        deltax = header.get('DELTAX')

        assert y
        assert firstx is not None
        assert not (lastx is None and deltax is None)

        npoints = len(y)
        if lastx is None:
            lastx = float(firstx) + (npoints - 1) * float(deltax)
        if deltax is None:
            deltax = (float(lastx) - float(firstx)) / (npoints - 1)

        # find YFACTOR, MINY, and MAXY
        miny = sys.float_info.max
        maxy = sys.float_info.min
        max_decimal = 0

        for string in y:
            value = float(string)
            try:
                index = string.index('.')
            except ValueError:
                index = 0

            decimal = len(string) - index - 1

            miny = min(miny, value)
            maxy = max(maxy, value)
            max_decimal = max(max_decimal, decimal)
        yfactor = 10 ** (-max_decimal)

        # write header with xydata specific values
        self._write_header({
            'MINX': firstx,
            'MAXX': lastx,
            'MINY': miny,
            'MAXY': maxy,
            'NPOINTS': npoints,
            'FIRSTY': y[0],
            'XFACTOR': 1.0,
            'YFACTOR': yfactor,
            'XUNITS': header.get('XUNITS', XUNITS[0]),
            'YUNITS': header.get('YUNITS', YUNITS[0]),
            'XYDATA': '(X++(Y..Y))'
        })

        # write the xydata
        self._write_xydata(y, npoints, firstx, deltax, max_decimal)

        # write the end
        self.buffer.write('##END=$$ End of the data block' + os.linesep)

    def _process_xypoints(self, header, x, y):
        assert x
        assert y

        firstx = x[0]
        firsty = y[0]
        lastx = x[-1]
        npoints = len(x)

        # find MINX, MAXX, MINY, MAXY
        minx = sys.float_info.max
        maxx = sys.float_info.min
        miny = sys.float_info.max
        maxy = sys.float_info.min
        for x_string, y_string in zip(x, y):
            try:
                x_float = float(x_string)
                minx = min(minx, x_float)
                maxx = max(maxx, x_float)
            except ValueError:
                continue

            try:
                y_float = float(y_string)
                miny = min(miny, y_float)
                maxy = max(maxy, y_float)
            except ValueError:
                continue

        # write header with xydata specific values
        self._write_header({
            'FIRSTX': firstx,
            'LASTX': lastx,
            'MINX': minx,
            'MAXX': maxx,
            'MINY': miny,
            'MAXY': maxy,
            'NPOINTS': npoints,
            'FIRSTY': firsty,
            'XUNITS': header.get('XUNITS', XUNITS[0]),
            'YUNITS': header.get('YUNITS', YUNITS[0]),
            'XYPOINTS': '(XY..XY)'
        })

        # write the xypoints
        self._write_xypoints(x, y)

        # write the end
        self.buffer.write('##END=$$ End of the data block' + os.linesep)

    def _process_ntuples(self, header, tables):
        self._prepare_calculation_header(tables[0], False)
        self._write_header({
            'NTUPLES': '(XY..XY)',
            #'VAR_NAME': '',
            #'SYMBOL': 'X, Y',
            # 'VAR_TYPE': 'INDEPENDENT, DEPENDENT',
            # 'VAR_FORM': 'AFFN, AFFN',
            #'VAR_DIM': ', ',
            'UNITS': f'{header.get('XUNITS', XUNITS[0])}, {header.get('YUNITS', YUNITS[0])}',
            #'FIRST': '',
            #'LAST': '',
        })

        for i, table in enumerate(tables):
            x = table.get('x')
            y = table.get('y')
            assert x
            assert y

            header = table.get('header')

            npoints = len(x)
            # write header for one page

            self._write_header({
                'PAGE': header['NTUPLES_PAGE_HEADER_VALUE'],
                'NPOINTS': npoints,
                'DATA TABLE': '(XY..XY)'

            })

            # write the xypoints
            self._write_xypoints(x, y)

        # write the end
        self.buffer.write(f'##END NTUPLES' + os.linesep)
        self.buffer.write('##END=$$ End of the data block' + os.linesep)

    def _write_header(self, header):
        for key, value in header.items():
            if value is not None:
                self.buffer.write(f'##{key}={value}' + os.linesep)


    def write_comment_header(self, header):
        self.buffer.write('$$ ' + '-' * 20 + '\n')
        for value in header:
            if value is not None:
                for line in value.split('\n'):
                    self.buffer.write(f'$$ {line}{os.linesep}')
        self.buffer.write('$$ ' + '-' * 20 + '\n')

    def _write_xydata(self, y, npoints, firstx, deltax, max_decimal):
        for i in range(0, npoints, self.nline):
            x = float(firstx) + i * float(deltax)

            line = str(x)
            for j in range(self.nline):
                if i + j < npoints:
                    string = y[i + j]
                    try:
                        index = string.index('.')
                    except ValueError:
                        index = 0
                    decimal = len(string) - index - 1
                    line += ',' + string.replace('.', '') + (max_decimal - decimal) * '0'

            self.buffer.write(line + os.linesep)

    def _write_xypoints(self, x, y):
        for x_string, y_string in zip(x, y):
            if not x_string.strip() and not y_string.strip():
                continue
            line = x_string + ', ' + y_string
            self.buffer.write(line + os.linesep)

    def write(self) -> bytes | str:
        if self.buffer is None:
            return b''
        return self.buffer.getvalue()

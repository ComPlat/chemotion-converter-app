import io
import os
import sys

from .base import Writer
from .. import __title__, __version__
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

    def process_ntuples_tables(self) -> list:
        """
        Prepares single jdx for all NTUPLES data tables
        """
        tables = [table for table in self.tables if table.get('header', {}).get('DATA CLASS') == 'NTUPLES']
        if len(tables) == 0:
            return tables
        self.buffer = io.StringIO()
        header = tables[0].get('header', {})
        self._prepare_main_header(header)
        self._process_ntuples(header, tables)
        return tables

    def process_table(self, table):
        """
        Prepares single jdx for one file
        :param table: Converted table to be processed
        """
        self.buffer = io.StringIO()
        header = table.get('header', {})

        self._prepare_main_header(header)

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
            'JCAMP-DX': f'5.00 $$ {__title__} ({__version__})',
            'DATA TYPE': header.get('DATA TYPE', DATA_TYPES[0]),
            'DATA CLASS': header.get('DATA CLASS', DATA_CLASSES[0]),
            'ORIGIN': header.get('ORIGIN', ''),
            'OWNER': header.get('OWNER', '')
        }
        for key in header:
            key_upper = key.upper()
            if key_upper not in jcamp_header:
                jcamp_header[key_upper] = header[key]
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
        data_type = header.get('DATA TYPE', DATA_TYPES[0])
        self._write_header({
            'NTUPLES': data_type,
            'VAR_NAME': '',
            'SYMBOL': 'X, Y',
            'VAR_TYPE': 'INDEPENDENT, DEPENDENT',
            'VAR_FORM': 'AFFN, AFFN',
            'VAR_DIM': ', ',
            'UNITS': f'{header.get('XUNITS', XUNITS[0])}, {header.get('YUNITS', YUNITS[0])}',
            'FIRST': '',
            'LAST': '',
        })
        for i, table in enumerate(tables):
            x = table.get('x')
            y = table.get('y')
            assert x
            assert y

            npoints = len(x)
            # write header for one page

            self._write_header({
                'PAGE': f'{i + 1}',
                'NPOINTS': npoints,
                'DATA TABLE': '(XY..XY), PEAKS'

            })

            # write the xypoints
            self._write_xypoints(x, y)

        # write the end
        self.buffer.write(f'##END NTUPLES={data_type}' + os.linesep)
        self.buffer.write('##END=$$ End of the data block' + os.linesep)

    def _write_header(self, header):
        for key, value in header.items():
            if value is not None:
                self.buffer.write(f'##{key}={value}' + os.linesep)

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
            line = x_string + ', ' + y_string
            self.buffer.write(line + os.linesep)

    def write(self) -> bytes | str:
        if self.buffer is None:
            return b''
        return self.buffer.getvalue()

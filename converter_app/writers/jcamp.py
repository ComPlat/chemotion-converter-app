import os
import sys

from .. import __title__, __version__
from .base import Writer


class JcampWriter(Writer):

    nline = 12

    data_types = (
        'INFRARED SPECTRUM',
        'RAMAN SPECTRUM',
        'INFRARED PEAK TABLE',
        'INFRARED INTERFEROGRAM',
        'INFRARED TRANSFERED SPECTRUM',
        'NMR FID',
        'NMR SPECTRUM',
        'NMR PEAK TABLE',
        'NMP PEAK ASSIGNMENTS',
        'MASS SPECTRUM',
        'CONTINUOUS MASS SPECTRUM',
        'THERMOGRAVIMETRIC ANALYSIS',
        'UV-VIS',
        'GEL PERMEATION CHROMATOGRAPHY',
        'CYCLIC VOLTAMMETRY',
    )

    data_classes = (
        'XYPOINTS',
        'XYDATA',
        'PEAK TABLE',
        'NTUPLES',
    )

    xunits = (
        '1/CM',
        'MICROMETERS',
        'NANOMETERS',
        'SECONDS',
        'HZ',
    )

    yunits = (
        'TRANSMITTANCE',
        'REFLECTANCE',
        'ABSORBANCE',
        'KUBELKA-MUNK',
        'COUNTS',
        'ARBITRARY UNITS',
    )

    @property
    def options(self):
        return {
            'DATA TYPE': self.data_types,
            'DATA CLASS': self.data_classes,
            'XUNITS': self.xunits,
            'YUNITS': self.yunits,
        }

    @property
    def suffix(self):
        return '.jdx'

    def process(self, header, data):
        self.write_header({
            'TITLE': data.get('title', 'Spectrum'),
            'JCAMP-DX': '5.00 $$ {} ({})'.format(__title__, __version__),
            'DATA TYPE': header.get('DATA TYPE', self.data_types[0]),
            'DATA CLASS': header.get('DATA CLASS', self.data_classes[0]),
            'ORIGIN': header.get('ORIGIN'),
            'OWNER': header.get('OWNER')
        })

        data_class = header.get('DATA CLASS', self.data_classes[0])
        if data_class == 'XYDATA':
            self.process_xydata(header, data)
        elif data_class in ['XYPOINTS', 'PEAK TABLE']:
            self.process_xypoints(header, data)
        elif data_class == 'NTUPLES':
            self.process_ntuples(header, data)

    def process_xydata(self, header, data):
        y = data.get('y')
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

        for i, string in enumerate(y):
            value = float(string)
            index = string.index('.')
            decimal = len(string) - index - 1

            miny = min(miny, value)
            maxy = max(maxy, value)
            max_decimal = max(max_decimal, decimal)
        yfactor = 10**(-decimal)

        # write header with xydata specific values
        self.write_header({
            'FIRSTX': firstx,
            'LASTX': lastx,
            'MINX': firstx,
            'MAXX': lastx,
            'MINY': miny,
            'MAXY': maxy,
            'NPOINTS': npoints,
            'DELTAX': deltax,
            'FIRSTY': y[0],
            'XFACTOR': 1.0,
            'YFACTOR': yfactor,
            'XUNITS': header.get('XUNITS', self.xunits[0]),
            'YUNITS': header.get('YUNITS', self.yunits[0]),
            'XYDATA': '(X++(Y..Y))'
        })

        # write the xydata
        self.write_xydata(y, npoints, firstx, deltax, max_decimal)

        # write the end
        self.buffer.write('##END=$$ End of the data block' + os.linesep)

    def process_xypoints(self, metadata, data):
        x = data.get('x')
        y = data.get('y')

        assert x is not None
        assert y is not None

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
            x_float, y_float = float(x_string), float(y_string)

            minx = min(minx, x_float)
            maxx = max(maxx, x_float)
            miny = min(miny, y_float)
            maxy = max(maxy, y_float)

        # write header with xydata specific values
        self.write_header({
            'FIRSTX': firstx,
            'LASTX': lastx,
            'MINX': minx,
            'MAXX': maxx,
            'MINY': miny,
            'MAXY': maxy,
            'NPOINTS': npoints,
            'FIRSTY': firsty,
            'XUNITS': metadata.get('XUNITS', self.xunits[0]),
            'YUNITS': metadata.get('YUNITS', self.yunits[0]),
            'XYPOINTS': '(XY..XY)'
        })

        # write the xypoints
        self.write_xypoints(x, y)

        # write the end
        self.buffer.write('##END=$$ End of the data block' + os.linesep)

    def process_ntuples(self, metadata, data):
        x = data.get('x')
        y = data.get('y')

        assert x is not None
        assert y is not None

        npoints = len(x)

        # find MINX, MAXX, MINY, MAXY
        minx = sys.float_info.max
        maxx = sys.float_info.min
        miny = sys.float_info.max
        maxy = sys.float_info.min
        for x_string, y_string in zip(x, y):
            x_float, y_float = float(x_string), float(y_string)

            minx = min(minx, x_float)
            maxx = max(maxx, x_float)
            miny = min(miny, y_float)
            maxy = max(maxy, y_float)

        # write header with ntuples specific values
        data_class = metadata.get('DATA CLASS', self.data_classes[0])
        self.write_header({
            'NTUPLES': data_class,
            'VAR_NAME': '',
            'SYMBOL': '',
            'VAR_TYPE': '',
            'VAR_FORM': '',
            'VAR_DIM': '',
            'UNITS': '',
            'FIRST': '',
            'LAST': '',
        })

        # write header for one page
        self.write_header({
            'PAGE': '1',
            'NPOINTS': npoints,
            'DATA TABLE': '(XY..XY), PEAKS'
        })

        # write the xypoints
        self.write_xypoints(x, y)

        # write the end
        self.buffer.write('##END NTUPLES={}'.format(data_class) + os.linesep)
        self.buffer.write('##END=$$ End of the data block' + os.linesep)

    def write_header(self, header):
        for key, value in header.items():
            if value is not None:
                self.buffer.write('##{}={}'.format(key, value) + os.linesep)

    def write_xydata(self, y, npoints, firstx, deltax, max_decimal):
        for i in range(0, npoints, self.nline):
            x = float(firstx) + i * deltax

            line = str(x)
            for j in range(self.nline):
                if i + j < npoints:
                    string = y[i+j]
                    index = string.index('.')
                    decimal = len(string) - index - 1
                    line += ',' + string.replace('.', '') + (max_decimal - decimal) * '0'

            self.buffer.write(line + os.linesep)

    def write_xypoints(self, x, y):
        for x_string, y_string in zip(x, y):
            line = x_string + ', ' + y_string
            self.buffer.write(line + os.linesep)

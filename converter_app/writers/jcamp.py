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
        'NMP PEAK ASSIGNMENTS'
    )

    data_classes = (
        'XYDATA',
        'XYPOINTS',
        'PEAK TABLE',
        'ASSIGNMENTS',
        'NTUPLES'
    )

    xunits = (
        '1/CM',
        'MICROMETERS',
        'NANOMETERS',
        'SECONDS',
        'HZ'
    )

    yunits = (
        'TRANSMITTANCE',
        'REFLECTANCE',
        'ABSORBANCE',
        'KUBELKA-MUNK',
        'ARBITRARY UNITS'
    )

    def write(self, data):
        metadata = {
            'TITLE': data.get('title', 'Spectrum'),
            'JCAMP-DX': '5.01 $$ {} ({})'.format(__title__, __version__),
            'DATA TYPE': 'INFRARED SPECTRUM',
            'DATA CLASS': 'XYDATA',
            'ORIGIN': data.get('origin'),
            'OWNER': data.get('owner'),
            'XUNITS': data.get('xunits', '1/CM'),
            'YUNITS': data.get('yunits', 'TRANSMITTANCE')
        }

        if 'x' in data:
            self.write_xypoints(metadata, data)
        else:
            self.write_xydata(metadata, data)

    def write_xydata(self, metadata, data):
        y = data.get('y')
        firstx = data.get('firstx')
        lastx = data.get('lastx')
        npoints = len(y)
        deltax = (float(lastx) - float(firstx)) / (npoints - 1)

        # find YFACTOR, MINY, and MAXY
        miny = sys.float_info.max
        maxy = sys.float_info.min
        max_decimal = 0
        for i, string in enumerate(y):
            x = float(firstx) + i * deltax
            value = float(string)
            index = string.index('.')
            decimal = len(string) - index - 1

            miny = min(miny, value)
            maxy = max(maxy, value)
            max_decimal = max(max_decimal, decimal)
        yfactor = 10**(-decimal)

        # update metadata with xydata specific values
        metadata.update({
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
            'XYDATA': '(X++(Y..Y))'
        })

        # write the metadata
        for key, value in metadata.items():
            if value is not None:
                self.buffer.write('##{}={}'.format(key, value) + os.linesep)

        # write the xydata
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

        # write the end
        self.buffer.write('##END=$$ End of the data block' + os.linesep)

    def write_xypoints(self, metadata, data):
        x = data.get('x')
        y = data.get('y')
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

        # update metadata with xydata specific values
        metadata.update({
            'FIRSTX': firstx,
            'LASTX': lastx,
            'MINX': minx,
            'MAXX': maxx,
            'MINY': miny,
            'MAXY': maxy,
            'NPOINTS': npoints,
            'FIRSTY': firsty,
            'XYPOINTS': '(XY..XY)'
        })

        # write the metadata
        for key, value in metadata.items():
            if value is not None:
                self.buffer.write('##{}={}'.format(key, value) + os.linesep)

        # write the xypoints
        for x_string, y_string in zip(x, y):
            line = x_string + ',' + y_string
            self.buffer.write(line + os.linesep)

        # write the end
        self.buffer.write('##END=$$ End of the data block' + os.linesep)

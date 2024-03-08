import logging
import re
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)

UNIT_EXTENSION = "_unit"


class TifReader(Reader):
    """
    Reads metadata from Tiff file images
    """
    identifier = 'tif_reader'
    priority = 96
    _parsed_values = None

    def check(self):
        result = False
        if self.file.suffix.lower() == '.tif' and self.file.mime_type == 'image/tiff':
            self._parsed_values = self._read_img()
            result = self._parsed_values is not None and len(self._parsed_values) > 0
        return result

    def _read_img(self):
        txt = re.sub(r'\\x[0-9a-f]{2}', '', str(self.file.content))

        txt = re.sub(r'^.+@@@@@@0\\r\\n', '', txt)
        lines = re.split(r'\\r\\n', txt)
        del lines[-1]
        return [x.split('=') for x in lines]

    def get_value(self, value):
        if self.float_de_pattern.match(value):
            # remove any digit group seperators and replace the comma with a period
            return value.replace('.', '').replace(',', '.')
        if self.float_us_pattern.match(value):
            # just remove the digit group seperators
            return value.replace(',', '')

        return None

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        for val in self._parsed_values:
            if len(val) == 1:
                num_val = self.get_value(val[0])
                if num_val is not None:
                    table['rows'].append([len(table['rows']), float(num_val)])
            else:
                table['metadata'][val[0]] = '='.join(val[1:])
            table['header'].append(f"{'='.join(val)}")

        table['columns'].append({
            'key': '0',
            'name': 'Idx'
        })
        table['columns'].append({
            'key': '1',
            'name': 'Number'
        })

        return tables


Readers.instance().register(TifReader)

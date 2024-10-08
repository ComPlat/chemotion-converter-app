import logging

from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)


class VsiReader(Reader):
    """
        Implementation of the Vsm Reader. It extends converter_app.readers.helper.base.Reader
    """
    identifier = 'vsi_reader'
    priority = 10

    def check(self):
        return self.file.suffix.lower() == '.xml'

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        key = ''
        unit = {}
        for line in self.file.fp.readlines():
            row = line.decode('utf-8').strip()
            if row.find('<Data key') >= 0:
                key_start = row.find('key=')+5
                key_end = row.find('"', key_start)
                key = row[key_start:key_end]
                value_start = (row.find('>')+1) if row.find('>') >= 0 else -1
                value_end = row.find('</Data>')
                table['metadata'][key] = row[value_start:value_end]
            elif row.find('<Value>') >= 0:
                value_start = row.find('<Value>')+7
                value_end = row.find('</Value>')
                table['metadata'][key] = row[value_start:value_end]
            elif row.find('<Unit>') >= 0:
                value_start = row.find('<Unit>') + 6
                value_end = row.find('</Unit>')
                unit[key] = row[value_start:value_end]
            elif row.find('</Data>') >= 0:
                value_start = (row.find('>') + 1) if row.find('>') >= 0 else -1
                value_end = row.find('</Data>')
                if value_end == 0:
                    continue
                table['metadata'][key] = row[value_start:value_end]

            if key in unit and table['metadata'][key] != '' and unit[key] not in table['metadata'][key]:
                table['metadata'][key] += ' ' + unit[key]

        return tables


Readers.instance().register(VsiReader)

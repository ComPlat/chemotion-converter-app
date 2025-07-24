import logging

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class SquidReader(Reader):
    """
    Reads and converts .dat files for SQUID measurement
    """

    identifier = 'squid_reader'
    priority = 10

    def check(self):
        return self.file.encoding != 'binary' and self.file.suffix.lower() == '.dat'

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        phase = ''
        for line in self.file.fp.readlines():
            row = line.decode(self.file.encoding).rstrip()
            match phase:
                case 'header':
                    if row.startswith(';'):
                        table['header'].append(row[2:])
                    else:
                        phase = 'metadata'
                case 'metadata':
                    if row == '[Data]':
                        phase = 'columns'
                    else:
                        if ',' not in row:
                            continue
                        meta_type, rest = row.split(',', 1)
                        match meta_type:
                            case 'INFO':
                                value, key = rest.rsplit(',', 1)
                                table['metadata'][meta_type + '.' + key] = value
                            case 'DATATYPE' | 'FIELDGROUP' | 'STARTUPAXIS':
                                key, value = rest.split(',', 1)
                                table['metadata'][meta_type + '.' + key] = value
                            case _:
                                table['metadata'].add_unique(meta_type, rest)
                case 'columns':
                    for idx, name in enumerate(item.strip() for item in row.split(',')):
                        table['columns'].append({
                            'key': str(idx),
                            'name': name
                        })
                    phase = 'data'
                case 'data':
                    table['rows'].append([self.get_value(value) for value in row.split(',')])
                case _:
                    if row == '[Header]':
                        phase = 'header'



        return tables


Readers.instance().register( SquidReader )

import logging

from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.unit_converter import convert_units, search_terms_matrix

logger = logging.getLogger(__name__)


class CsmReader(Reader):
    """
        Implementation of the Csm Reader. It extends converter_app.readers.helper.base.Reader
    """
    identifier = 'csm_reader'
    priority = 10

    def check(self):
        return self.file.suffix.lower() == '.html'

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        begin = False
        key = ''
        for line in self.file.fp.readlines():
            row = line.decode('utf-8').strip()
            if not begin:
                if row.find('<tbody>') >= 0:
                    begin = True
            else:
                if row.find('</tbody>') >= 0:
                    break
                if row.find('<td>') >= 0:
                    if key == '':
                        key = row[4:-5]
                        for term in search_terms_matrix:
                            if key == term[1]:
                                key = term[0]
                    else:
                        value = row[4:-5]
                        table['metadata'][key] = value
                        key = ''
        table['metadata'] = convert_units(table['metadata'], 1)
        return tables


Readers.instance().register(CsmReader)

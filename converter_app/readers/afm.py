import logging
import re

from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.unit_converter import convert_units, search_terms_matrix

logger = logging.getLogger(__name__)


class AfmReader(Reader):
    """
    Implementation of the Afm Reader. It extends converter_app.readers.helper.base.Reader
    """
    identifier = 'afm_reader'
    priority = 10

    def check(self):
        return self.file.suffix.lower() == '.spm'

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        header = False
        lines = []

        for line in self.file.fp.readlines():
            lines.append(line)
            try:
                row = line.decode('utf-8').strip()
            except UnicodeDecodeError:
                continue

            if re.search(r'[^-<|>!?+*:.,#@%&~_"\'/\\a-zA-Z0-9\[\](){}\s]', row):
                continue

            if len(row) > 1 and row[1] == '*':
                header = True

            if header:
                table['header'].append(row[2:])
                header = False
            else:
                k_v = [x.strip() for x in row[1:].split(':', 1)]
                table['metadata'].add_unique(k_v[0], k_v[-1])

        extracted_table = self.append_table(tables)
        for term in search_terms_matrix:
            value = table['metadata'].get(term[2]) if table['metadata'].get(term[2]) is not None else ''
            extracted_table['metadata'].add_unique(term[0], value)

        extracted_table['metadata'] = convert_units(extracted_table['metadata'], 2)

        return tables


Readers.instance().register(AfmReader)

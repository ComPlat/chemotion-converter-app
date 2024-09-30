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
                k_v = row[1:].split(':')
                table['metadata'].add_unique(k_v[0], k_v[-1])

        extracted_table = self.append_table(tables)
        extracted_table['metadata'] = self._extract_information_afm(lines)

        return tables

    @staticmethod
    def _extract_information_afm(lines):
        # Create the table with search_terms_matrix
        table = [[term[0], ''] for term in search_terms_matrix]

        # Simplify the file content
        end_marker = b'*File list end'
        try:
            end_index = next(i for i, line in enumerate(lines) if end_marker in line)
            lines = lines[:end_index]
        except StopIteration:
            return {}

        # Converting the lines into a list of strings
        simplified_data = [line.decode('utf-8', errors='ignore').strip() for line in lines]

        # Search the simplified data list for the search terms
        for term in search_terms_matrix:
            search_term = term[2]
            if search_term:
                AfmReader._find_search_term(search_term, simplified_data, table, term)

        # Create info_dict from table
        info_dict = {row[0]: row[1] for row in table}
        info_dict = convert_units(info_dict, 2)
        return info_dict

    @staticmethod
    def _find_search_term(search_term, simplified_data, table, term):
        for line in simplified_data:
            if search_term in line:
                # Finde den Wert nach dem Suchbegriff
                match = re.search(rf'{re.escape(search_term)}\s*:\s*(.*)', line)
                if match:
                    value = match.group(1).strip()
                    # Finde die Zeile in der Tabelle, die dem Suchbegriff entspricht
                    for row in table:
                        if row[0] == term[0]:
                            row[1] = value
                            break
                break


Readers.instance().register(AfmReader)

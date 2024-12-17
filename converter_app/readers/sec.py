import logging
import re
from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)

UNIT_EXTENSION = "_unit"


class SecReader(Reader):
    """
    Reads Sec Files
    """
    identifier = 'sec_reader'
    priority = 95

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self._has_header = False
        self._has_first_value = False
        self._is_table_empty = True
        self._is_calibration = 0

    def check(self):
        """
        :return: True if it fits
        """
        result = False
        if self.file.suffix.lower() == '.txt' and self.file.mime_type == 'text/plain':
            first_lines = [self.file.string.splitlines()[0], self.file.string.splitlines()[1],
                           self.file.string.splitlines()[2]]
            result_a = 'Sample :' in first_lines[0] and 'Method settings :' in first_lines[1] and 'Sequence table :' in \
                       first_lines[2]
            result_b = 'Sample :' in first_lines[0] and 'Inject date :' in first_lines[1] and 'Inject volume :' in \
                       first_lines[2]

            result = result_a or result_b

        return result

    def _append_table(self, tables):
        self._has_header = False
        self._has_first_value = False
        self._is_table_empty = True

        return self.append_table(tables)

    def _handle_line(self, line, table):
        if line == 'Calibration Coefficients:':
            self._is_calibration = 2
            return False
        if self._is_calibration > 0:
            return self._set_calibration(line, table)
        return self._split_key_val(line, table)

    def _set_calibration(self, line, table):
        line_val = line.split(':')
        if line == '':
            self._is_calibration -= 1
        elif len(line_val) >= 2:
            self._is_table_empty = False
            table['header'].append(line)
            table['metadata'][line_val[0]] = line_val[1]

        return self._is_calibration > 0

    def _split_key_val(self, line, table):
        line_array = line.split('\t')
        key = None
        line_key = None
        counter = 0
        for word in line_array:
            if re.compile(r' :\s*$').search(word) or (word.endswith(":") and key is None):
                if key is None:
                    key = re.compile(r'\s*:\s*$').sub('', word)
                    line_key = key
                else:
                    key = f'({line_key}) { word.replace(" :", "")}'
                counter = 0
            elif key is not None:
                counter += 1
                if counter > 1:
                    key += UNIT_EXTENSION
                table['header'].append(f'{key}: {word}')
                table['metadata'][key] = word
                self._has_first_value = False
                self._has_header = False
            elif word == '' and len(line_array) > 1:
                table['header'].append(f' {line_array[1]}')
                table['metadata'][' - '] = line_array[1]

                self._is_table_empty = False
                return True
            else:
                if line == '':
                    return not self._has_first_value
                elif not self._has_header:
                    for header_str in line_array:
                        table['columns'].append({
                            'key': str(len(table['columns'])),
                            'name': header_str
                        })
                    self._has_header = True
                else:
                    for col_idx in range(len(table['columns'])):
                        if col_idx < len(line_array):
                            line_array[col_idx] = self.get_value(line_array[col_idx].replace(' ', ''))
                        else:
                            line_array.append('')

                    self._has_first_value = True
                    table['rows'].append(line_array)

                self._is_table_empty = False
                return True

        self._is_table_empty = False
        return True

    def prepare_tables(self):
        tables = []
        table = self._append_table(tables)

        for line in self.file.fp.readlines():
            line = line.decode(self.file.encoding).rstrip()
            if line.endswith('start :') or not self._handle_line(line, table):
                if self._is_table_empty:
                    tables.pop()
                table['metadata']['rows'] = str(len(table['rows']))
                table['metadata']['columns'] = str(len(table['columns']))
                table_name = line.replace('start :', '') or 'Unnamed'

                table = self._append_table(tables)
                table['header'].append(table_name)
                table['metadata']['table_name'] = table_name

        if self._is_table_empty:
            tables.pop()
        return tables


Readers.instance().register(SecReader)

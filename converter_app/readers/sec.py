import copy
import logging
import re

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

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
        self._is_multi_area_report = False
        self._detectors = {}
        self._detector_metadata = []

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
        origin_key = None
        line_key = None
        counter = 0
        for word_idx, word in enumerate(line_array):
            word = word.strip()
            if re.compile(r' :\s*$').search(word) or (word.endswith(":") and key is None):
                if key is None:
                    key = re.compile(r'\s*:\s*$').sub('', word)
                    line_key = key
                else:
                    key = f'({line_key}) {word.replace(" :", "")}'
                counter = 0
                origin_key = key
            elif key is not None:
                counter += 1
                if re.match(r'Detector \d+', key):
                    self._detectors[word] = {}

                if self._detector_metadata:
                    if len(self._detector_metadata) >= word_idx:
                        key = f'{origin_key}_DECT{word_idx}'
                        self._detectors[self._detector_metadata[word_idx - 1]][origin_key] = word
                    else:
                        key = f'{origin_key}{UNIT_EXTENSION}'
                        for i, v in self._detectors.items():
                            v[origin_key + UNIT_EXTENSION] = word
                elif counter > 1:
                    key += UNIT_EXTENSION

                table['header'].append(f'{key}: {word}')
                table['metadata'][key] = word
                self._has_first_value = False
                self._has_header = False
            elif word == '' and len(line_array) > 1:
                line_array = [x for x in line_array if x != '']
                table['header'].append(f' {", ".join(line_array)}')
                table['metadata'][' - '] = ", ".join(line_array)
                if all(x in self._detectors.keys() for x in line_array):
                    self._detector_metadata = line_array
                else:
                    self._detector_metadata = None
                self._is_table_empty = False
                return True
            else:
                self._detector_metadata = None
                if line == '':
                    if self._is_multi_area_report:
                        self._table_to_metadata(table)
                        return True
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

                table_name = line.replace('start :', '') or 'Unnamed'
                self._is_multi_area_report = table_name.startswith('Multi area report')

                table = self._append_table(tables)
                table['header'].append(table_name)
                table['metadata']['table_name'] = table_name

        if self._is_table_empty:
            tables.pop()
        return self._split_detector_data(tables)

    def _split_detector_data(self, tables):
        copied_tables = copy.deepcopy(tables)
        for idx, table in reversed(list(enumerate(tables))):
            if len(table['rows']) == 0:
                continue

            sort_obj = []
            det_idx = '_'
            group_column_count = 1
            current_group_position = 1
            # Phase: 'searching', 'measuring', 'applying'
            phase = 'searching'
            for col in table['columns']:
                col_name = col['name']
                match phase:
                    case 'searching':
                        if col_name in self._detectors:
                            det_idx = col_name
                            phase = 'measuring'
                    case 'measuring':
                        if col_name in self._detectors:
                            det_idx = col_name
                            phase = 'applying'
                        else:
                            group_column_count += 1
                    case _: # phase == 'applying'
                        if col_name in self._detectors:
                            det_idx = col_name
                            current_group_position = 1
                        elif current_group_position < group_column_count:
                            current_group_position += 1
                        else:
                            det_idx = '_'

                sort_obj.append(det_idx)
            copied_tables.pop(idx)
            for detext, values in self._detectors.items():
                if not any(det == detext for det in sort_obj):
                    continue  # Skip this detector if no columns match

                new_table = self.append_table([])
                new_table['metadata'] = table['metadata'] | values | {'__DETECTOR': detext}
                new_table['header'] = table['header']
                for row in table['rows']:
                    new_table['rows'].append(
                        [val for idx, val in enumerate(row) if sort_obj[idx] == detext or sort_obj[idx] == '_'])
                new_table['columns'] = [val for idx, val in enumerate(table['columns']) if
                                        sort_obj[idx] == detext or sort_obj[idx] == '_']
                copied_tables.insert(idx, new_table)
        return copied_tables

    def _table_to_metadata(self, table):
        if not self._has_first_value:
            return
        self._has_header = False
        self._has_first_value = False
        try:
            for r_i, row in enumerate(table['rows']):
                for i, value in enumerate(row):
                    table.add_metadata(f"{table['columns'][i]['name']}_({r_i})", value)
        except IndexError:
            pass
        table['rows'] = []
        table['columns'] = []


Readers.instance().register(SecReader)

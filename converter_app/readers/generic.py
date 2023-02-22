import logging
import os
import re
import json

from .base import Reader as Readerbase

from ..models import Reader as Reader

logger = logging.getLogger(__name__)


class GenericReader(Readerbase):
    identifier = 'generic_reader'
    priority = 105

    _DELIMITER_PLACEHOLDER = "####DELIMITER_PLACEHOLDER####"
    _STRING_TOKEN_PLACEHOLDER = "XXXXDELIMITERPLACEHOLDERXXXX"

    mode = None
    _commend_mode = False

    def _check_identifyer(self, s, i):
        if (i.get('match') == 'exact'):
            return i.get('value') == s
        if (i.get('match') == 'regex'):
            rv = re.compile(i.get('value'))
            return rv.search(s)
        return False

    def check(self):
        if self.file.string is not None:
            file_lines = self.file.fp.readlines()

            for reader in Reader.list(self.client_id):
                parser_dict = reader.as_dict
                file_ext = re.split('[,\s]+',
                                    parser_dict.get('identifiers', {}).get('meta', {}).get('file_extension', ''))
                if file_ext == [''] or self.file.suffix in file_ext:
                    result = True
                    for line_check in parser_dict.get('identifiers', {}).get('content', []):
                        line = file_lines[line_check['lineNumber'] - 1]
                        row = line.decode(self.file.encoding).rstrip()
                        if not self._check_identifyer(row, line_check):
                            result = False
                            break

                    if result:
                        self.parser_dict = parser_dict
                        self.lines = file_lines
                        self.identifier = parser_dict['title']
                        logger.debug('result=%s', result)
                        return result

        logger.debug('result=%s', False)
        return False

    def _split_identifier(self, row, sep):
        if sep.get('match') == 'exact':
            return row.replace(sep.get('value'), self._DELIMITER_PLACEHOLDER)
        if (sep.get('match') == 'regex'):
            return re.sub(sep.get('value'), self._DELIMITER_PLACEHOLDER, row)
        return row

    def _get_split_free(self, row):
        sep = self.parser_dict.get('delimiters').get('free_identifier')
        return self._split_identifier(row, sep)

    def _split_row(self, row):
        lc = self.parser_dict.get('commend').get('line_commend')
        if lc.get('value') != "":
            row = self._split_identifier(row, lc).split(self._DELIMITER_PLACEHOLDER)[0]

        string_list = None
        if self.parser_dict.get('delimiters').get('ignore_within_quotes'):
            string_list = re.finditer(r"([\"'])(?:(?=(\\?))\2.)*?\1", row)
            row = re.sub(r"([\"'])(?:(?=(\\?))\2.)*?\1", self._STRING_TOKEN_PLACEHOLDER, row)

        delimiter_options = self.parser_dict.get('delimiters').get('options')
        if delimiter_options[-1].get('active', False):
            row = self._get_split_free(row)
        for deli in delimiter_options[0:-1]:
            if deli.get('active', False):
                row = re.sub(deli.get('symbol') + '+', self._DELIMITER_PLACEHOLDER, row)

        if string_list is not None:
            for match in string_list:
                row = row.replace(self._STRING_TOKEN_PLACEHOLDER, match.group(), 1)

        return row.split(self._DELIMITER_PLACEHOLDER)

    def _split_metadata_row(self, row):
        return list(filter(lambda x: len(x) > 0, self._split_row(row)))

    def _split_datatable_row(self, row, mode = None):
        if mode is None:
            mode = self.mode
        if mode.get('allow_empty_col'):
            return self._split_row(row)
        return self._split_metadata_row(row)

    def _append_table(self, tables):
        self.table = self.append_table(tables)

    def _check_new_mode(self, row, next_row):
        if self.mode is not None:
            return False
        for table in self.parser_dict.get('tables', []):
            if table.get('has_start_identifier', False):
                if not self._check_identifyer(row, table.get('start_identifier')):
                    return False
                else:
                    res = self._parse_table_row(next_row, table)
            elif table.get('has_col_header_row', False):
                res = self._parse_table_row(next_row, table)
            else:
                res = self._parse_table_row(row, table)

            if res is not None:
                self.mode = table
                return True
            return False


    def _parse_table_row(self, row, table, add_to_table=False):
        row_list = self._split_datatable_row(row, table)
        if len(row_list) <= table.get('max_number_of_col') and len(row_list) >= table.get('min_number_of_col'):
            if table.get('allow_str_col') != "":
                str_cols = list(set([int(x) for x in table.get('allow_str_col').split(',')]))
                str_cols.sort(reverse=True)
                all_cols = list(range(len(row_list)))

                for str_idx in str_cols:
                    all_cols.remove(str_idx)
                    res = re.findall(table.get('number_value_regex'), row_list[str_idx])
                    if len(res) == 1:
                        return None
                for idx in all_cols:
                    res = re.findall(table.get('number_value_regex'), table.get('number_value_regex'))
                    if len(res) != 1:
                        return None
                    row_list[idx] = self.get_value(res[0][0])

                if add_to_table:
                    self.table['rows'].append(row_list)
                return row_list
        return None


    def _check_end_mode(self, row, next_row):
        td_list = self.parser_dict.get('delimiters').get('table_delimiters')
        for td in td_list:
            if td.get('value') != '' and self._check_identifyer(row, td):
                return True
        if self.mode is None:
            return False
        if self._parse_table_row(row, self.mode) is None:
            self.mode = None
            return True
        return False

    def _check_commend_mode(self, row):
        multi_line_commend_start = self.parser_dict.get('commend').get('multi_line_commend_start')
        if multi_line_commend_start.get('value') == '':
            return self._commend_mode
        if not self._commend_mode and self._check_identifyer(row, multi_line_commend_start):
            self._commend_mode = True
            return self._commend_mode
        multi_line_commend_end = self.parser_dict.get('commend').get('multi_line_commend_start')
        if multi_line_commend_end.get('value') == '':
            multi_line_commend_end = multi_line_commend_start
        if self._commend_mode and self._check_identifyer(row, multi_line_commend_end):
            self._commend_mode = False
        return self._commend_mode

    def _add_key_to_meta(self, key, value):
        unique_key = key
        idx = 1
        while unique_key in self.table['metadata']:
            unique_key = "%s(%d)" % (key, idx)
            idx += 1
        self.table['metadata'][unique_key] = value

    def get_tables(self):
        tables = []
        self._append_table(tables)

        for line_idx in range(0, len(self.lines)):

            row = re.sub(r"^\s*", "", self.lines[line_idx].decode(self.file.encoding).rstrip())
            if line_idx + 1 < len(self.lines):
                next_row = re.sub(r"^\s*", "", self.lines[line_idx + 1].decode(self.file.encoding).rstrip())
            else:
                next_row = ''
            if self._check_new_mode(row, next_row):
                self._commend_mode = False
                self.table['header'].append(row)
                if self.mode.get('has_col_header_row', False):
                    for header_str in self._split_metadata_row(row):
                        self.table['columns'].append({
                            'key': "%d" % len(self.table['columns']),
                            'name': header_str
                        })
                    self._check_commend_mode(row)
                    continue
            elif self._check_end_mode(row, next_row):
                self._append_table(tables)

            temp_commend_mode = self._commend_mode
            if (self._check_commend_mode(row) or temp_commend_mode) and self.mode is None:
                self.table['header'].append(row)
                continue


            if self.mode is None:
                self.table['header'].append(row)
                row_vals = self._split_metadata_row(row)
                if len(row_vals) > 0:
                    if len(row_vals) == 1:
                        row_vals.insert(0, '')

                    if len(row_vals[0]) == 0:
                        row_vals[0] = 'NO KEY'

                    if len(row_vals) == 2:
                        self._add_key_to_meta(row_vals[0], row_vals[1])
                    elif len(row_vals) > 2:
                        for (v_id, v) in enumerate(row_vals[1:]):
                            self._add_key_to_meta("%s.col_%d" % (row_vals[0], v_id), v)
            else:
                self._parse_table_row(row, self.mode, True)

        for table in tables:
            if table['rows'] and len(table['columns']) == 0:
                table['columns'] = [{
                    'key': str(idx),
                    'name': 'Column #{}'.format(idx)
                } for idx, value in enumerate(table['rows'][0])]

            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))

        return tables

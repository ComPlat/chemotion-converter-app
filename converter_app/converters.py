import datetime
import logging
import os
import re
from collections import defaultdict

from converter_app.models import Profile

logger = logging.getLogger(__name__)


class CalculationError(Exception):
    pass


class Converter:
    """
    Converter object checks if the profile matches to filedata and runs the converting process
    """

    def __init__(self, profile, file_data):
        self._output_index_offset = None
        self._has_loop_cache = None
        self._loop_match_cache = None
        self._joined_headers = None
        self.profile = profile
        self.matches = []
        self.reaction_variation_matches = []
        self.tables = []
        self.file_metadata = file_data.get('metadata', {})
        self.input_tables = file_data.get('tables', [])
        self.profile_output_tables = self.profile.data.get('tables', [])
        self.output_tables = []

        self.identifiers = self._prepare_identifier()
        self._reaction_variation_identifiers = self._prepare_reaction_variation_identifier()

    def prepare(self):
        # Precomputed once so the loop helpers don't redo the same
        # (output_index, input_index) work on every call. Without these,
        # _get_output_table_index re-scans every output/input pair on every
        # invocation and _check_loop_condition is repeated for the same
        # arguments from _prepare_identifier, _prepare_tables, and
        # _get_output_table_index — quadratic-to-cubic with looped tables.
        self._joined_headers = [
            os.linesep.join(t.get('header', [])).rstrip() for t in self.input_tables
        ]
        self._has_loop_cache = {
            i: self._compute_has_loop(i) for i in range(len(self.profile_output_tables))
        }
        self._loop_match_cache = {}
        return

    def _prepare_tables(self, index):
        # match the output Table to the input tables and adjust the tableIndexes t_get_output_table_indexo the input table
        for input_table_index, _ in enumerate(self.input_tables):
            if not self._check_loop_condition(index, input_table_index):
                continue


    def _prepare_reaction_variation_identifier(self):
        return self.profile.data.get('reactionVariations', {}).get('identifiers', [])

    def _prepare_identifier(self):
        return self.profile.data.get('identifiers', [])

    def _has_loop(self, index):
        return self._has_loop_cache.get(index, False)

    def _compute_has_loop(self, index):
        if len(self.profile_output_tables) <= index:
            return False
        if self.profile_output_tables[index].get('loopType') == 'all':
            return self.profile_output_tables[index].get('matchTables')
        loop_header = self.profile_output_tables[index]['table'].get('loop_header')
        loop_metadata = self.profile_output_tables[index]['table'].get('loop_metadata')
        loop_theader = self.profile_output_tables[index]['table'].get('loop_theader')
        return any(x for x in [loop_header, loop_metadata, loop_theader])

    def _check_loop_condition(self, index, input_table_index):
        key = (index, input_table_index)
        if key in self._loop_match_cache:
            return self._loop_match_cache[key]
        self._loop_match_cache[key] = self._compute_check_loop_condition(index, input_table_index)
        return self._loop_match_cache[key]

    def _compute_check_loop_condition(self, index, input_table_index):
        if self.profile_output_tables[index].get('loopType') != 'all':
            loop_header = self.profile_output_tables[index]['table'].get('loop_header', [])
            for header in loop_header:
                if not header.get('column'):
                    return False
                table_index = header['column'].get('tableIndex')
                column_index = header['column'].get('columnIndex')
                if (table_index is None or column_index is None or len(self.input_tables) <= table_index
                        or len(self.input_tables[table_index].get('columns', [])) <= column_index):
                    # No Input Table Column with given Ids found
                    return False
                if table_index == input_table_index:
                    continue
                column_name = self.input_tables[table_index].get('columns')[column_index].get('name')
                if (len(self.input_tables[input_table_index].get('columns', [])) <= column_index
                or column_name != self.input_tables[input_table_index].get('columns')[column_index].get('name')):
                    return False

            loop_theader = self.profile_output_tables[index]['table'].get('loop_theader', [])
            for theader in loop_theader:
                match, _ = self._search_regex(theader, input_table_index)
                if match is None:
                    return False

            loop_metadata = self.profile_output_tables[index]['table'].get('loop_metadata', [])
            for metadata in loop_metadata:
                if not metadata.get('value') or not metadata.get('table'):
                    return False
                key = metadata.get('value')
                if metadata.get('ignoreValue'):
                    if not key in self.input_tables[input_table_index].get('metadata', {}):
                        return False
                else:
                    table_index = self.profile_output_tables[index]['inputTableIndex']
                    value = self.input_tables[table_index].get('metadata', {}).get(key, None)
                    if value != self.input_tables[input_table_index].get('metadata', {}).get(key, None):
                        return False
            return True
        return True

    def _compute_output_index_offsets(self):
        offsets = {}
        result_index = 0
        for output_table_index in range(len(self.profile_output_tables)):
            offsets[output_table_index] = result_index
            if self._has_loop(output_table_index):
                for input_table_index in range(len(self.input_tables)):
                    if self._check_loop_condition(output_table_index, input_table_index):
                        result_index += 1
            else:
                result_index += 1
        return offsets

    def match(self):
        self.matches = self._match(self.identifiers)
        return len(self.matches)

    def match_reaction_variation_identifier(self):
        self.reaction_variation_matches = self._match_identifier(self._reaction_variation_identifiers)

    def _match(self, identifiers):
        """

        :return:
        """

        matches = []
        for identifier in identifiers:
            if not identifier.get('optional'):
                match = self.match_identifier(identifier)
                if match is False:
                    return False

            # store match
                matches.append(match)

        # if everything matched, return how many identifiers matched
        return matches

    def _match_identifier(self, identifiers):
        """

        :return:
        """

        matches = []
        for identifier in identifiers:
            match = self.match_identifier(identifier)
            if match is False and not identifier.get('optional'):
                # return immediately if one (non optional) identifier does not match
                return False

            if match and 'value' in match:
                match_operations = identifier.get('operations', [])
                for match_operation in match_operations:
                    match['value'] = self._run_identifier_operation(match['value'], match_operation)

            # store match
            matches.append({
                'identifier': identifier,
                'result': match
            })

        # if everything matched, return how many identifiers matched
        return matches

    def match_identifier(self, identifier, in_idx = None):
        """
        Checks if single identifier matches
        :param identifier: Identifier profile object
        :return: Boolean if matches
        """
        if identifier.get('type') == 'fileMetadata':
            return self._match_file_metadata(identifier, self.file_metadata)
        if identifier.get('type') == 'tableMetadata':
            return self._match_table_metadata(identifier, self.input_tables, in_idx)
        if identifier.get('type') == 'tableHeader':
            return self._match_table_header(identifier, self.input_tables, in_idx)

        return False

    def _match_file_metadata(self, identifier, metadata):
        input_key = identifier.get('key')
        input_value = metadata.get(input_key)
        if input_key and input_value:
            value = self._match_value(identifier, input_value)
            if value:
                return {
                    'value': value
                }

        return False

    def _match_table_metadata(self, identifier, input_tables, input_table_index=None):
        if input_table_index is None:
            input_table_index = identifier.get('tableIndex')
        input_table = input_tables[input_table_index]
        if input_table is not None:
            input_key = identifier.get('key', None)
            input_value = input_table.get('metadata', {}).get(input_key, None)
            if input_key is not None and input_value is not None:
                value = self._match_value(identifier, input_value)
                if value:
                    return {
                        'value': value,
                        'tableIndex': input_table_index
                    }

        return False

    def _match_table_header(self, identifier, input_tables, input_table_index=None):
        if input_table_index is None:
            input_table_index = identifier.get('tableIndex')
        input_table = input_tables[input_table_index]
        if input_table is not None:
            # try to get the line_number from the identifier
            try:
                line_number = int(identifier.get('lineNumber'))
            except (ValueError, TypeError):
                line_number = None

            if line_number is None:
                # use the whole header
                header = os.linesep.join(input_table['header']).rstrip()
            else:
                # use only the provided line
                try:
                    # the interface counts from 1
                    header = input_table['header'][line_number - 1].rstrip()
                except IndexError:
                    # the line in the header does not exist
                    return False

            if header:
                # try to match the value
                value = self._match_value(identifier, header)

                if value:
                    # if no line number was provided, find the line number for the value
                    if line_number is None:
                        line_number = self._get_line_number(input_table['header'], value)

                    return {
                        'value': value,
                        'tableIndex': input_table_index,
                        'lineNumber': line_number,
                    }

        return False

    def _match_value(self, identifier, value):
        if value is not None:
            value = str(value)
            if identifier.get('isRegex') or identifier.get('match') == 'regex':
                pattern = identifier.get('value')
                if str(pattern).startswith('^') or str(pattern).endswith('$'):
                    match = re.search(pattern, str(value), re.MULTILINE)
                else:
                    match = re.search(pattern, str(value))
                logger.debug('match_value pattern="%s" value="%s" match=%s', pattern, value, bool(match))
                if match:
                    try:
                        return match.group(1).strip()
                    except IndexError:
                        return match.group(0).strip()
                else:
                    return False
            elif identifier.get('match') == 'any':
                logger.debug('match_value identifier="%s", value="any" result=%s', identifier.get('value'), bool(value))
                return value if value else False

            else:  # match == 'exact'
                result = (value == str(identifier.get('value')))
                logger.debug('match_value identifier="%s", value="%s" result=%s', identifier.get('value'), value,
                             result)
                return value if result else False
        else:
            return False

    def get_reaction_variation_matches(self):
        values = []
        for [sample_id, value_id, unit_id] in self.profile.data.get('reactionVariations', {}).get('elements', []):
            value = next((x for x in self.reaction_variation_matches if x['identifier']['id'] == value_id), {}).get('result', {}).get('value')
            sample = next((x for x in self.reaction_variation_matches if x['identifier']['id'] == sample_id), {}).get('result', {}).get('value')
            unit = next((x for x in self.reaction_variation_matches if x['identifier']['id'] == unit_id), {}).get('result', {}).get('value')
            values.append([sample, value, unit])
        return {
            'samples': values
        }


    def process(self):
        self.prepare()
        for in_idx in range(len(self.input_tables)):
            for output_table_index, output_table in enumerate(self.profile_output_tables):
                if output_table['inputTableIndex'] == in_idx or self._check_loop_condition(output_table_index, in_idx):
                    header = self._process_prepare_header(output_table, in_idx)
                    self._process_prepare_metadata(header, output_table_index)





    def _process(self):
        """
        Runs converting process efficiently.
        """



        ntuples_count = defaultdict(int)  # Track NTUPLES_ID occurrences
        self.match_reaction_variation_identifier()
        for output_table_index, output_table in enumerate(self.output_tables):
            # --- Prepare header and metadata ---
            header = self._process_prepare_header(output_table)
            self._process_prepare_metadata(header, output_table_index)

            # --- Extract table info ---
            table_data = output_table.get('table', {})
            x_column = table_data.get('xColumn')
            y_column = table_data.get('yColumn')
            x_operations = table_data.get('xOperations', [])
            y_operations = table_data.get('yOperations', [])

            # --- Prepare rows (reuse existing lists if possible) ---
            x_rows = []
            y_rows = []
            for operation in x_operations:
                if operation.get('type') == 'column':
                    operation['rows'] = []
            for operation in y_operations:
                if operation.get('type') == 'column':
                    operation['rows'] = []

            # --- Prepare data ---
            self._process_prepare_data(x_column, x_operations, x_rows,
                                       y_column, y_operations, y_rows)

            # --- Apply operations ---
            applied_operators = {
                "applied_x_operator": False,
                "applied_y_operator": False,
                "applied_operator_failed": False,
                "x_operations_description": table_data.get('xOperationsDescription'),
                "y_operations_description": table_data.get('yOperationsDescription')
            }

            try:
                for operation in x_operations:
                    applied_operators["applied_x_operator"] |= self._run_operation(x_rows, operation)
                for operation in y_operations:
                    applied_operators["applied_y_operator"] |= self._run_operation(y_rows, operation)
            except CalculationError:
                applied_operators['applied_x_operator'] = False
                applied_operators['applied_y_operator'] = False
                applied_operators['applied_operator_failed'] = True
                x_rows.clear()
                y_rows.clear()

            # --- Optimized NTUPLES page header logic ---
            if header.get('DATA CLASS') == 'NTUPLES':
                page_header = header.get('NTUPLES_PAGE_HEADER')

                if page_header == '___TABLE_NAME':
                    header['NTUPLES_PAGE_HEADER_VALUE'] = f'TABLE: {x_column["tableIndex"]}'

                elif page_header == '___+':
                    this_id = header['NTUPLES_ID']
                    header['NTUPLES_PAGE_HEADER_VALUE'] = ntuples_count.get(this_id, 0)
                    ntuples_count[this_id] += 1

                else:
                    # Cache input metadata for fast access
                    input_metadata = {}
                    if x_column is not None:
                        table_index = x_column.get("tableIndex")
                        if table_index is not None and table_index < len(self.input_tables):
                            input_metadata = self.input_tables[table_index].get('metadata', {})
                    key_value = input_metadata.get(page_header, 'UNKNOWN')
                    header['NTUPLES_PAGE_HEADER_VALUE'] = f"{page_header}= {key_value}"

            # --- Append table efficiently ---
            table_dict = {
                'header': header,
                'x': x_rows,
                'y': y_rows
            }
            table_dict.update(applied_operators)

            self.tables.append(table_dict)

    def _process_prepare_data(self, x_column, x_operations, x_rows, y_column, y_operations, y_rows):
        """
        Efficiently fills x_rows, y_rows, and operation rows using direct table/column access.
        Avoids scanning all input tables and columns.
        """

        def check_indexes(tabel_index, column_index):
            if len(self.input_tables) <= tabel_index:
                return False
            tabel = self.input_tables[table_index]
            if len(tabel['rows']) == 0:
                return False
            row = tabel['rows'][0]
            if len(row) <= column_index:
                return False
            return True

        # --- Fill x_rows directly ---
        if x_column:
            table_index = x_column['tableIndex']
            col_index = x_column['columnIndex']
            if check_indexes(table_index, col_index):
                table = self.input_tables[table_index]
                for row in table['rows']:
                    x_rows.append(self.get_value(row, col_index))

        # --- Fill y_rows directly ---
        if y_column:
            table_index = y_column['tableIndex']
            col_index = y_column['columnIndex']
            if check_indexes(table_index, col_index):
                table = self.input_tables[table_index]
                for row in table['rows']:
                    y_rows.append(self.get_value(row, col_index))

        # --- Fill x_operations rows directly ---
        for operation in x_operations:
            if operation.get('type') == 'column' and operation.get('column'):
                col = operation['column']
                col_index =col['columnIndex']
                table_index = col['tableIndex']
                if check_indexes(table_index, col_index):
                    table = self.input_tables[table_index]
                    op_rows = operation.setdefault('rows', [])
                    for row in table['rows']:
                        op_rows.append(self.get_value(row, col_index))

        # --- Fill y_operations rows directly ---
        for operation in y_operations:
            if operation.get('type') == 'column' and operation.get('column'):
                col = operation['column']
                col_index =col['columnIndex']
                table_index = col['tableIndex']
                if check_indexes(table_index, col_index):
                    table = self.input_tables[table_index]
                    op_rows = operation.setdefault('rows', [])
                    for row in table['rows']:
                        op_rows.append(self.get_value(row, col_index))


    def _process_prepare_metadata(self, header, output_table_index):
        # merge the metadata from the profile (header) with the metadata
        # extracted using the identifiers (see self.match)
        for identifier in self.identifiers:
            match_result = match.get('result')
            if match_result:
                match_output_key = match.get('identifier', {}).get('outputKey')
                match_output_table_index = match.get('identifier', {}).get('outputTableIndex')
                match_value = match_result.get('value')
                if match_output_key and (
                        output_table_index == match_output_table_index or
                        match_output_table_index is None
                ):
                    header[match_output_key] = match_value


    def _process_prepare_header(self, output_table, in_idx):
        header = {}
        for key, value in output_table.get('header', {}).items():
            if isinstance(value, dict):
                # this is a table identifier, e.g. FIRSTX
                match = self.match_identifier(value, in_idx)
                if match:
                    header[key] = match['value']
            else:
                header[key] = value
        return header


    def _run_operation(self, rows, operation):
        for i, row in enumerate(rows):
            str_value = None
            if operation.get('type') == 'column':
                try:
                    str_value = operation['rows'][i]
                except IndexError:
                    pass
            elif operation.get('type') == 'value':
                str_value = operation.get('value')
            elif operation.get('type') == 'metadata_value':
                str_value = self.input_tables[int(operation.get('table'))]['metadata'].get(operation.get('value'))
            elif operation.get('type') == 'header_value':
                table_id = 0
                if operation.get('table') is not None:
                    table_id = int(operation.get('table'))
                match, str_value = self._search_regex(operation, table_id)
                if match is not None:
                    if len(match.regs) > 1:
                        str_value = match[1]
                    else:
                        str_value = match[0]
            else:
                raise ValueError(f"Unknown operation type: {operation.get('type')}")
            try:
                op_value = float(str_value)
            except (TypeError, ValueError):
                if not operation.get('ignore_missing_values'):
                    raise CalculationError("Calculation could not be executed")
                return False

            if op_value:
                rows[i] = str(self.apply_operation(row, op_value, operation.get('operator')))

        return True

    def _search_regex(self, operation, table_id):
        match = None
        str_value = None
        try:
            line_number = int(operation.get('line', ''))
            header = self.input_tables[table_id]['header'][line_number - 1].rstrip()
        except (TypeError, ValueError, IndexError):
            header = self._joined_headers[table_id]
        pattern = operation.get('regex')
        if header is not None and pattern is not None:
            str_value = header
            match = re.search(pattern, str_value)
        return match, str_value

    def _run_identifier_operation(self, value, operation):
        op_value = operation.get('value')
        if op_value:
            return self.apply_operation(value, op_value, operation.get('operator'))
        return value


    def apply_operation(self, value, op_value, op_operator):
        """
        Apply mathematical operator
        :param value: numeric value left
        :param op_value: numeric value right
        :param op_operator: mathematical operator
        :return:
        """
        try:
            float_value = float(self._fix_float(value))

            if op_operator == '+':
                return float_value + float(op_value)
            if op_operator == '-':
                return float_value - float(op_value)
            if op_operator == '*':
                return float_value * float(op_value)
            if op_operator == ':':
                return float_value / float(op_value)
        except ValueError:
            pass
        return None


    def get_input_table(self, index, input_tables):
        if index is not None:
            try:
                if int(index) >= len(input_tables):
                    return None
                return input_tables[int(index)]
            except KeyError:
                return None
        return None

    def _get_line_number(self, header, value):
        # if line_number is None:
        for i, line in enumerate(header):
            if value in line:
                # again we count from 1
                return i + 1
        return -1


    def get_value(self, row, column_index):
        """
        Parses value in row at index into string
        :param row:
        :param column_index: Index
        :return: converted value as string
        """
        return self._fix_float(row[column_index])


    @staticmethod
    def _fix_float(value):
        return str(value).replace(',', '.').replace('e', 'E')


    @classmethod
    def match_profile(cls, client_id, file_data):
        """
        Iterates over all profiles and checks which matches
        :param client_id: [str] Username
        :param file_data: File content to be converted
        :return: Matching converter obj
        """
        converter = None
        matches = 0
        latest_profile_uploaded = 0
        current_converter = None
        for profile in Profile.list_including_default(client_id):
            if profile.isDisabled:
                continue
            try:
                current_converter = cls(profile, file_data)
                current_matches = current_converter.match()
            except (ValueError, TypeError, IndexError):
                current_matches = False
            try:
                profile_uploaded = datetime.datetime.fromisoformat(
                    profile.as_dict['data']['metadata'].get('uploaded')).timestamp()
            except (ValueError, TypeError):
                profile_uploaded = 1
            logger.info('profile=%s matches=%s', profile.id, current_matches)
            if (current_matches is not False and
                    (current_matches > matches or current_matches == matches and
                     profile_uploaded > latest_profile_uploaded)):
                matches = max(matches, current_matches)
                latest_profile_uploaded = profile_uploaded
                converter = current_converter

        return converter

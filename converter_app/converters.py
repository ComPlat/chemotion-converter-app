import datetime
import logging
import os
import re
from collections import defaultdict
from typing import LiteralString
import astropy.units as u

from converter_app.models import Profile
from converter_app.utils import normalize_unit

logger = logging.getLogger(__name__)

# imperial units (e.g. deg_F) are not in astropy's default registry; enable them globally
u.imperial.enable()


class CalculationError(Exception):
    pass


class Converter:
    """
    Converter object checks if the profile matches to filedata and runs the converting process
    """

    def __init__(self, profile, file_data):
        self._output_index_offset = None
        self._has_loop_cache = None
        self._joined_headers = None
        self.profile = profile
        self.matches = []
        self.reaction_variation_matches = []
        self._tables = defaultdict(list)
        self.file_metadata = file_data.get('metadata', {})
        self.input_tables = file_data.get('tables', [])
        self.attachments = file_data.get('attachments', [])
        self.profile_output_tables = self.profile.data.get('tables', [])
        self.output_tables = []

        self.identifiers = self._prepare_identifier()
        self._reaction_variation_identifiers = self._prepare_reaction_variation_identifier()

    def get_matches(self, rdf=False, dataset=False):
        return_matches = []
        for match in self.matches:
            if rdf and match['identifier']['isRdfOutput']:
                return_matches.append(match)
            if dataset and match['identifier']['isDatasetOutput']:
                return_matches.append(match)
        return return_matches

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

        self.matches = self._resolve_all_identifiers(self.identifiers)

    @property
    def tables(self):
        sorted_items = sorted(
            self._tables.items(),
            key=lambda item: item[0][0]
        )

        for (tb_idx, keys), out_table_res in sorted_items:
            output_table = self.profile_output_tables[tb_idx]
            is_ntuples = output_table.get('loopOutput') == 'SINGLE FILE (NTUPLES)' and output_table['loopType'] != 'none'
            if is_ntuples:
                yield out_table_res
            else:
                for table in out_table_res:
                    yield table

    def _prepare_reaction_variation_identifier(self):
        return self.profile.data.get('reactionVariations', {}).get('identifiers', [])

    def _prepare_identifier(self):
        return self.profile.data.get('identifiers', [])

    def _compute_has_loop(self, index):
        if len(self.profile_output_tables) <= index:
            return False
        return self.profile_output_tables[index].get('loopType') != 'none'

    def _compute_check_loop_condition(self, index, input_table_index):
        """
        Return a tuple that says whether this output table should process the
        current input table. The first item is the match flag; remaining items
        are grouping values used to build the output table key.
        """
        # "all" loop tables accept every input table without further checks.
        if self.profile_output_tables[index].get('loopType') == 'all':
            return (True, )

        if self.profile_output_tables[index].get('loopType') != 'none':
            # For looped tables, every configured loop selector must match the
            # input table. Group selectors append their value to group_values so
            # matching input tables are collected into the same output bucket.
            group_values = [True]
            loop_header = self.profile_output_tables[index]['table'].get('loop_header', [])
            for header in loop_header:
                if not header.get('column'):
                    return (False, )
                column_name = header['column']

                # loop_header entries require a column with the configured name
                # to exist in the candidate input table.
                has_col_name = any(
                    col.get('name') == column_name for col in self.input_tables[input_table_index].get('columns', []))
                if not has_col_name:
                    return (False, )

            loop_theader = self.profile_output_tables[index]['table'].get('loop_theader', [])
            for theader in loop_theader:
                # Header regex selectors must match. Unless ignoreValue is set,
                # the captured value becomes part of the grouping key.
                match, _ = self._search_regex(theader, input_table_index)
                if not match:
                    return (False, )
                if not theader.get('ignoreValue'):
                    group_values.append(match)

            loop_metadata = self.profile_output_tables[index]['table'].get('loop_metadata', [])
            for metadata in loop_metadata:
                # Metadata selectors can either contribute a grouping value or
                # require an exact metadata value on the input table.
                if not metadata.get('metadata'):
                    return (False, )
                key = metadata.get('metadata')
                if not key in self.input_tables[input_table_index].get('metadata', {}):
                    return (False, )
                match_mode = metadata.get('matchMode')
                if match_mode == 'group':
                    value = self.input_tables[input_table_index].get('metadata', {}).get(key, None)
                    group_values.append(value)
                if match_mode == 'exact':
                    value = self.input_tables[input_table_index].get('metadata', {}).get(key, None)
                    if metadata.get('value') != value:
                        return (False, )

            return tuple(group_values)
        elif input_table_index == self.profile_output_tables[index]['inputTableIndex']:
            # Non-looped tables only process their configured input table.
            return (True, )
        return (False, )

    def match(self):
        matches = self._match(self.identifiers)
        if isinstance(matches, list):
            return len(matches)
        return False

    def match_reaction_variation_identifier(self):
        self.reaction_variation_matches = self._resolve_all_identifiers(self._reaction_variation_identifiers)

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

    def _resolve_all_identifiers(self, identifiers):
        """

        :return:
        """

        matches = []
        for identifier in identifiers:

            if identifier.get('optional'):
                # return immediately if one (non optional) identifier does not match

                match = self._resolve_identifier(identifier)
                # store match
                matches.append({
                    'identifier': identifier,
                    'result': match
                })

        # if everything matched, return how many identifiers matched
        return matches

    def _resolve_identifier(self, identifier, in_idx=None):
        match = self.match_identifier(identifier, in_idx)
        if match and 'value' in match:
            match_operations = identifier.get('operations', [])
            for match_operation in match_operations:
                match['value'] = self._run_identifier_operation(match['value'], match_operation)
        return match

    def match_identifier(self, identifier, in_idx=None):
        """
        Checks if single identifier matches
        :param in_idx:
        :param identifier: Identifier profile object
        :return: Boolean if matches
        """
        res_value = False
        if identifier.get('type') == 'fileMetadata':
            res_value = self._match_file_metadata(identifier, self.file_metadata)
        if identifier.get('type') == 'tableMetadata':
            res_value = self._match_table_metadata(identifier, self.input_tables, in_idx)
        if identifier.get('type') == 'tableHeader':
            res_value = self._match_table_header(identifier, self.input_tables, in_idx)
        if res_value and identifier.get('outputKey', '').startswith('___unit___'):
            enum_units = identifier.get('outputEnum', [])
            in_list = [u.Unit(normalize_unit(x['label'])) for x in enum_units]
            unit = u.Unit(normalize_unit(res_value['value']))
            try:
                idx = in_list.index(unit)
                res_value['value'] = enum_units[idx]['key']
            except ValueError:
                res_value['value'] = None



        return res_value

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
                return self._solve_regex(identifier.get('value'), value)
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

    @staticmethod
    def _solve_regex(pattern, value: str) -> LiteralString | str | bool:
        if str(pattern).startswith('^') or str(pattern).endswith('$'):
            match = re.search(pattern, str(value), re.MULTILINE)
        else:
            match = re.search(pattern, str(value))
        logger.debug('match_value pattern="%s" value="%s" match=%s', pattern, f'{value[:10]}...', bool(match))
        if match:
            try:
                return match.group(1).strip()
            except IndexError:
                return match.group(0).strip()
        else:
            return False

    def get_reaction_variation_matches(self):
        values = []
        for [sample_id, value_id, unit_id] in self.profile.data.get('reactionVariations', {}).get('elements', []):
            value = next((x for x in self.reaction_variation_matches if x['identifier']['id'] == value_id), {}).get(
                'result', {}).get('value')
            sample = next((x for x in self.reaction_variation_matches if x['identifier']['id'] == sample_id), {}).get(
                'result', {}).get('value')
            unit = next((x for x in self.reaction_variation_matches if x['identifier']['id'] == unit_id), {}).get(
                'result', {}).get('value')
            values.append([sample, value, unit])
        return {
            'samples': values
        }

    def process(self):
        self.prepare()
        ntuples_header = dict()
        for in_idx in range(len(self.input_tables)):
            for output_table_index, output_table in enumerate(self.profile_output_tables):
                group_values = self._compute_check_loop_condition(output_table_index, in_idx)
                if group_values[0]:
                    output_table_key = (output_table_index, group_values)
                    header = self._process_prepare_header(output_table, output_table_key, in_idx, ntuples_header)
                    table_data = output_table.get('table', {})
                    x_column = table_data.get('xColumn')
                    y_column = table_data.get('yColumn')
                    x_operations = table_data.get('xOperations', [])
                    y_operations = table_data.get('yOperations', [])

                    # --- Prepare rows (reuse existing lists if possible) ---
                    for operation in x_operations:
                        if operation.get('type') == 'column':
                            operation['rows'] = []
                    for operation in y_operations:
                        if operation.get('type') == 'column':
                            operation['rows'] = []
                    x_rows = self._process_prepare_data(x_column, x_operations, in_idx)
                    y_rows = self._process_prepare_data(y_column, y_operations, in_idx)

                    # --- Prepare data ---

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
                            applied_operators["applied_x_operator"] |= self._run_operation(x_rows, operation, in_idx)
                        for operation in y_operations:
                            applied_operators["applied_y_operator"] |= self._run_operation(y_rows, operation, in_idx)
                    except CalculationError:
                        applied_operators['applied_x_operator'] = False
                        applied_operators['applied_y_operator'] = False
                        applied_operators['applied_operator_failed'] = True
                        x_rows.clear()
                        y_rows.clear()

                    # --- Append table efficiently ---
                    table_dict = {
                        'header': header,
                        'x': x_rows,
                        'y': y_rows
                    }
                    table_dict.update(applied_operators)

                    self._tables[output_table_key].append(table_dict)

    def _process_prepare_data(self, column, operations, in_idx):
        """
        Efficiently fills rows and operation rows using direct table/column access.
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

        rows = []

        # --- Fill x_rows directly ---
        if column:
            table_index = in_idx
            col_index = column['columnIndex']
            if check_indexes(table_index, col_index):
                table = self.input_tables[table_index]
                for row in table['rows']:
                    rows.append(self.get_value(row, col_index))

        # --- Fill x_operations rows directly ---
        for operation in operations:
            if operation.get('type') == 'column' and operation.get('column'):
                col = operation['column']
                col_index = col['columnIndex']
                table_index = in_idx
                if check_indexes(table_index, col_index):
                    table = self.input_tables[table_index]
                    op_rows = operation.setdefault('rows', [])
                    for row in table['rows']:
                        op_rows.append(self.get_value(row, col_index))
        return rows

    def _process_prepare_metadata(self, header, output_table, in_idx, is_ntuples):
        # merge the metadata from the profile (header) with the metadata
        # extracted using the identifiers (see self.match)
        for match in self.matches:
            table_uuid = output_table['uuid']
            if not match['identifier']['isDatatableOutput'] or table_uuid not in match['identifier'][
                'outputTableIndex']:
                continue
            match_output_key = match.get('identifier', {}).get('outputDatatableKey')

            if match_output_key in header and (not match['identifier']['isLoobDatatableOutput'] or match['identifier']['isFirstMatch']):
                match_result = False
            elif not match['identifier']['isLoobDatatableOutput']:
                match_result = match['result']
            else:
                match_result = self._resolve_identifier(match['identifier'], in_idx) or match['result']

            if match_result:
                if match_output_key:
                    match_value = match_result.get('value')
                    if not is_ntuples or (not match['identifier']['isLoobDatatableOutput'] or match['identifier']['isFirstMatch']):
                        header[match_output_key] = match_value
                    else:
                        if match_output_key not in header:
                            header[match_output_key] = []
                        header[match_output_key].append(match_value)

    def _process_prepare_ntuples_header(self, output_table, output_table_idx, in_idx):
        header = {}
        page_header = output_table.get('nTuplePageHeader', '___+')
        header['NTUPLES_PAGE_HEADER'] = page_header
        if page_header == '___TABLE_NAME':
            header['PAGE'] = f'TABLE: {in_idx}'

        elif page_header == '___+':
            header['PAGE'] = len(self._tables[output_table_idx])

        else:
            # Cache input metadata for fast access
            input_metadata = {}
            if in_idx is not None and in_idx < len(self.input_tables):
                input_metadata = self.input_tables[in_idx].get('metadata', {})
            key_value = input_metadata.get(page_header, 'UNKNOWN')
            header['PAGE'] = f"{page_header}= {key_value}"
        return header

    def _process_prepare_header(self, output_table, output_table_key, in_idx, ntuples_header):
        header = {}
        is_ntuples = output_table.get('loopOutput') == 'SINGLE FILE (NTUPLES)' and output_table['loopType'] != 'none'
        if is_ntuples:
            header = self._process_prepare_ntuples_header(output_table, output_table_key, in_idx)
            if output_table_key not in ntuples_header:
                ntuples_header[output_table_key] = header
            else:
                self._process_prepare_metadata(ntuples_header[output_table_key], output_table, in_idx, is_ntuples)
                return header

        for key, value in output_table.get('header', {}).items():
            if isinstance(value, dict):
                # this is a table identifier, e.g. FIRSTX
                match = self.match_identifier(value, in_idx)
                if match:
                    header[key] = match['value']
            else:
                header[key] = value

        self._process_prepare_metadata(header, output_table, in_idx, is_ntuples)
        return header

    def _run_operation(self, rows, operation, in_idx):
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
                str_value = self.input_tables[in_idx]['metadata'].get(operation.get('value'))
            elif operation.get('type') == 'header_value':
                match, str_value = self._search_regex(operation, in_idx)
                if match is not None:
                    str_value = match
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
            match = self._solve_regex(pattern, str_value)
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
            except (ValueError, TypeError, IndexError) as e:
                current_matches = False
            try:
                profile_uploaded = datetime.datetime.fromisoformat(
                    profile.as_dict['data'][-1]['metadata'].get('uploaded')).timestamp()
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

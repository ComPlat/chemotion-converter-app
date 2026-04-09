import copy
import datetime
import os
import re
from collections import defaultdict

from astropy import units as u
from astropy.units import UnitConversionError

from converter_app.models import Profile
from converter_app.readers.helper.unit_finder import UnitFinder

import logging
logger = logging.getLogger(__name__)


class CalculationError(Exception):
    pass


class Converter:
    """
    Converter object checks if the profile matches to filedata and runs the converting process
    """

    def __init__(self, profile, file_data):
        self.profile = profile
        self.matches = []
        self.tables = []
        self.file_metadata = file_data.get('metadata', {})
        self.input_tables = file_data.get('tables', [])
        self.input_units = file_data.get('units', [])
        self.profile_units = self.profile.data.get('units', [])
        self.profile_data_units = self.profile.data.get('data', {}).get('units', [])
        self.profile_output_tables = self.profile.data.get('tables', [])
        self.output_tables = []
        self.output_table_profile_indexes = []
        self.unit_finder = UnitFinder(ignore_dimless=False)
        self._prepare_identifier()


        for output_table_index, output_table in enumerate(self.profile_output_tables):
            if self._has_loop(output_table_index):
                self._prepare_tables(output_table_index)
            else:
                self.output_table_profile_indexes.append(output_table_index)
                self.output_tables.append(output_table)

    def _prepare_tables(self, index):
        # match the output Table to the input tables and adjust the tableIndexes to the input table
        for input_table_index, _ in enumerate(self.input_tables):
            if not self._check_loop_condition(index, input_table_index):
                continue
            output_table = copy.deepcopy(self.profile_output_tables[index])
            output_table_table = output_table.get('table')
            if output_table_table:
                if 'xColumn' in output_table_table:
                    output_table_table['xColumn']['tableIndex'] = input_table_index
                if 'yColumn' in output_table_table:
                    output_table_table['yColumn']['tableIndex'] = input_table_index
                for x_operation in output_table_table.get('xOperations', []):
                    if x_operation.get('column', False):
                        x_operation['column']['tableIndex'] = input_table_index
                for y_operation in output_table_table.get('yOperations', []):
                    if y_operation.get('column', False):
                        y_operation['column']['tableIndex'] = input_table_index

            self.output_table_profile_indexes.append(index)
            self.output_tables.append(output_table)

    def _prepare_identifier(self):
        profile_identifiers = self.profile.data.get('identifiers', [])
        self.identifiers = []
        for identifier in profile_identifiers:
            output_table_index = identifier.get('outputTableIndex')
            if output_table_index is None:
                # if no outputTableIndex was set this identifier is valid for every table
                # no adjustment has to be done
                self.identifiers.append(identifier)
            else:
                if self._has_loop(output_table_index):
                    # adjust this identifier for every input table
                    for i, input_table_index in enumerate(
                            idx for idx in range(len(self.input_tables))
                            if self._check_loop_condition(output_table_index, idx)
                    ):
                        # make a copy of the identifier and adjust the outputTableIndex
                        identifier_copy = copy.deepcopy(identifier)
                        identifier_copy['outputTableIndex'] = (i + self._get_output_table_index(output_table_index))

                        # adjust the (input)tableIndex as well if it was not null
                        if identifier_copy.get('tableIndex') is not None:
                            identifier_copy['tableIndex'] = input_table_index

                        self.identifiers.append(identifier_copy)
                else:
                    identifier['outputTableIndex'] = self._get_output_table_index(output_table_index)
                    self.identifiers.append(identifier)

    def _has_loop(self, index):
        if len(self.profile_output_tables) <= index:
            return False
        if self.profile_output_tables[index].get('loopType') == 'all':
                return self.profile_output_tables[index].get('matchTables')
        else:
            loop_header = self.profile_output_tables[index]['table'].get('loop_header')
            loop_metadata = self.profile_output_tables[index]['table'].get('loop_metadata')
            loop_theader = self.profile_output_tables[index]['table'].get('loop_theader')
            return any(x for x in [loop_header, loop_metadata, loop_theader])


    def _check_loop_condition(self, index, input_table_index):
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
                    table_index = int(metadata.get('table'))
                    value = self.input_tables[table_index].get('metadata', {}).get(key, None)
                    if value != self.input_tables[input_table_index].get('metadata', {}).get(key, None):
                        return False
            return True
        return True

    def _get_output_table_index(self, index: int):
        result_index = 0
        for output_table_index, output_table in enumerate(self.profile_output_tables):
            if output_table_index == index:
                return result_index
            if self._has_loop(output_table_index):
                for input_table_index, _ in enumerate(self.input_tables):
                    if self._check_loop_condition(output_table_index, input_table_index):
                        result_index += 1
            else:
                result_index += 1
        return result_index

    def match(self):
        """

        :return:
        """
        for identifier in self.identifiers:
            match = self.match_identifier(identifier)
            if match is False and not identifier.get('optional'):
                # return immediately if one (non optional) identifier does not match
                return False

            if match and 'value' in match:
                match_operations = identifier.get('operations', [])
                for match_operation in match_operations:
                    match['value'] = self._run_identifier_operation(match['value'], match_operation)

            # store match
            self.matches.append({
                'identifier': identifier,
                'result': match
            })

        # if everything matched, return how many identifiers matched
        return len(self.matches)

    def match_identifier(self, identifier):
        """
        Checks if single identifier matches
        :param identifier: Identifier profile object
        :return: Boolean if matches
        """
        if identifier.get('type') == 'fileMetadata':
            return self._match_file_metadata(identifier, self.file_metadata)
        if identifier.get('type') == 'tableMetadata':
            return self._match_table_metadata(identifier, self.input_tables)
        if identifier.get('type') == 'tableHeader':
            return self._match_table_header(identifier, self.input_tables)

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

    def _match_table_metadata(self, identifier, input_tables):
        input_table_index = identifier.get('tableIndex')
        input_table = self.get_input_table(input_table_index, input_tables)
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

    def _match_table_header(self, identifier, input_tables):
        input_table_index = identifier.get('tableIndex')
        input_table = self.get_input_table(input_table_index, input_tables)
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

    def process(self):
        """
        Runs converting process efficiently.
        """

        ntuples_count = defaultdict(int)  # Track NTUPLES_ID occurrences

        for output_table_index, output_table in enumerate(self.output_tables):
            # --- Prepare header and metadata ---
            header = self._process_prepare_header(output_table)
            self._process_prepare_metadata(header, output_table_index)

            # --- Extract table info ---
            table_data = output_table.get('table', {})
            profile_output_table_index = self.output_table_profile_indexes[output_table_index]
            x_column = table_data.get('xColumn')
            y_column = table_data.get('yColumn')
            x_unit_result = self._prepare_unit_operations(
                output_table_index,
                profile_output_table_index,
                'X',
                x_column,
                table_data.get('xOperations', []),
                table_data.get('xOperationsDescription'),
            )
            y_unit_result = self._prepare_unit_operations(
                output_table_index,
                profile_output_table_index,
                'Y',
                y_column,
                table_data.get('yOperations', []),
                table_data.get('yOperationsDescription'),
            )
            x_operations = x_unit_result['operations']
            y_operations = y_unit_result['operations']
            x_operations_description = x_unit_result['descriptions']
            y_operations_description = y_unit_result['descriptions']

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
                "x_operations_description": x_operations_description,
                "y_operations_description": y_operations_description
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
        for match in self.matches:
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


    def _process_prepare_header(self, output_table):
        header = {}
        for key, value in output_table.get('header', {}).items():
            if isinstance(value, dict):
                # this is a table identifier, e.g. FIRSTX
                match = self.match_identifier(value)
                if match:
                    header[key] = match['value']
            else:
                header[key] = value
        return header

    def _prepare_unit_operations(
        self,
        output_table_index,
        profile_output_table_index,
        axis,
        column,
        operations,
        operation_descriptions=None,
    ):
        prepared_operations = [copy.deepcopy(operation) for operation in operations]
        prepared_descriptions = self._copy_operation_descriptions(operation_descriptions)
        if not self._uses_si_unit_logic(prepared_operations, operation_descriptions):
            return self._build_prepared_unit_result(prepared_operations, prepared_descriptions)

        profile_unit = self._get_profile_unit_assignment(profile_output_table_index, axis, column)
        if profile_unit is None:
            return self._build_prepared_unit_result(prepared_operations, prepared_descriptions)

        if self._get_input_unit_by_uuid(profile_unit.get('uuid')) is not None:
            return self._build_prepared_unit_result(prepared_operations, prepared_descriptions)

        unit_mode = str(profile_unit.get('unitMode', '')).strip()
        if unit_mode == 'Base':
            base_correction = self._resolve_base_mode_correction(profile_unit)
            if base_correction is None or base_correction.get('conversion_factor') is None:
                logger.warning(
                    'No matching input unit found for Base mode. output_table_index=%s axis=%s profile_unit_uuid=%s',
                    output_table_index,
                    axis,
                    profile_unit.get('uuid'),
                )
                corrected_operations = self._replace_si_unit_operations(prepared_operations, [self._build_nan_operation()])
                corrected_descriptions = self._append_auto_correction_descriptions(
                    prepared_descriptions,
                    self._build_failed_unit_correction_descriptions(output_table_index, axis, profile_unit),
                )
                return self._build_prepared_unit_result(corrected_operations, corrected_descriptions)

            logger.info(
                'Using temporary Base mode conversion factor. output_table_index=%s axis=%s profile_unit_uuid=%s factor=%s',
                output_table_index,
                axis,
                profile_unit.get('uuid'),
                base_correction['conversion_factor'],
            )
            corrected_operations = self._apply_base_mode_temporary_factor(
                prepared_operations,
                profile_unit,
                base_correction['conversion_factor'],
            )
            corrected_descriptions = self._append_auto_correction_descriptions(
                prepared_descriptions,
                self._build_base_unit_correction_descriptions(
                    output_table_index,
                    axis,
                    profile_unit,
                    base_correction['input_unit'],
                    base_correction['conversion_factor'],
                    corrected_operations,
                ),
            )
            return self._build_prepared_unit_result(corrected_operations, corrected_descriptions)

        if unit_mode == 'Found':
            found_correction = self._resolve_found_mode_correction(profile_unit)
            if found_correction is None:
                logger.warning(
                    'No convertible input unit found for Found mode. output_table_index=%s axis=%s profile_unit_uuid=%s',
                    output_table_index,
                    axis,
                    profile_unit.get('uuid'),
                )
                corrected_operations = self._replace_si_unit_operations(prepared_operations, [self._build_nan_operation()])
                corrected_descriptions = self._append_auto_correction_descriptions(
                    prepared_descriptions,
                    self._build_failed_unit_correction_descriptions(output_table_index, axis, profile_unit),
                )
                return self._build_prepared_unit_result(corrected_operations, corrected_descriptions)

            logger.info(
                'Using temporary Found mode conversion. output_table_index=%s axis=%s profile_unit_uuid=%s operations=%s',
                output_table_index,
                axis,
                profile_unit.get('uuid'),
                found_correction['operations'],
            )
            corrected_operations = self._replace_si_unit_operations(
                prepared_operations,
                found_correction['operations'],
            )
            corrected_descriptions = self._append_auto_correction_descriptions(
                prepared_descriptions,
                self._build_found_unit_correction_descriptions(
                    output_table_index,
                    axis,
                    profile_unit,
                    found_correction['input_unit'],
                    corrected_operations,
                ),
            )
            return self._build_prepared_unit_result(corrected_operations, corrected_descriptions)

        return self._build_prepared_unit_result(prepared_operations, prepared_descriptions)

    @staticmethod
    def _uses_si_unit_logic(operations, operation_descriptions=None):
        for operation in operations:
            if operation.get('source') == 'siUnits':
                return True

        if not operation_descriptions:
            return False

        for description in operation_descriptions:
            if '[SI Units]' in str(description):
                return True

        return False

    def _get_profile_unit_assignment(self, output_table_index, axis, column):
        normalized_axis = str(axis).upper()
        column_index = self._to_int((column or {}).get('columnIndex'))
        matching_units = []

        for profile_unit in self.profile_units:
            profile_axis = str(profile_unit.get('axis', '')).upper()
            profile_output_index = self._to_int(profile_unit.get('outputTableIndex'))
            if profile_axis != normalized_axis:
                continue
            if profile_output_index is not None and profile_output_index != output_table_index:
                continue
            matching_units.append(profile_unit)

        if column_index is None:
            return matching_units[0] if matching_units else None

        for profile_unit in matching_units:
            unit_column_index = self._to_int(profile_unit.get('inputColumn', {}).get('columnIndex'))
            if unit_column_index == column_index:
                return profile_unit

        return matching_units[0] if matching_units else None

    def _resolve_base_mode_correction(self, profile_unit):
        input_unit = self._find_preferred_input_unit(
            profile_unit,
            lambda candidate: self._shares_base_unit(candidate, profile_unit),
        )
        if input_unit is None:
            return None
        return {
            'input_unit': input_unit,
            'conversion_factor': self._to_float(input_unit.get('conversion_factor')),
        }

    def _resolve_found_mode_correction(self, profile_unit):
        preferred_index = self._get_profile_data_unit_index(profile_unit.get('uuid'))
        target_found = profile_unit.get('found')
        if not target_found:
            return None

        if preferred_index is not None and preferred_index < len(self.input_units):
            preferred_unit = self.input_units[preferred_index]
            operations = self._build_linear_unit_operations(preferred_unit.get('found'), target_found)
            if operations is not None:
                return {
                    'input_unit': preferred_unit,
                    'operations': operations,
                }

        for base_only in (True, False):
            for index, input_unit in enumerate(self.input_units):
                if index == preferred_index:
                    continue
                if base_only and not self._shares_base_unit(input_unit, profile_unit):
                    continue
                operations = self._build_linear_unit_operations(input_unit.get('found'), target_found)
                if operations is not None:
                    return {
                        'input_unit': input_unit,
                        'operations': operations,
                    }

        return None

    def _build_linear_unit_operations(self, source_found, target_found):
        source_unit = self.unit_finder.resolve_unit(str(source_found))
        target_unit = self.unit_finder.resolve_unit(str(target_found))
        if source_unit is None or target_unit is None:
            return None

        converted_zero = self._convert_unit_value(0, source_unit, target_unit)
        converted_one = self._convert_unit_value(1, source_unit, target_unit)
        if converted_zero is None or converted_one is None:
            return None

        factor = converted_one - converted_zero
        offset = converted_zero
        operations = []

        if not self._is_close(factor, 1.0):
            operations.append({
                'operator': '*',
                'source': 'siUnits',
                'type': 'value',
                'value': str(factor),
            })
        if not self._is_close(offset, 0.0):
            operations.append({
                'operator': '+',
                'source': 'siUnits',
                'type': 'value',
                'value': str(offset),
            })

        return operations

    @staticmethod
    def _convert_unit_value(value, source_unit, target_unit):
        quantity = value * source_unit

        try:
            return quantity.to(target_unit).value
        except (TypeError, ValueError, UnitConversionError):
            pass

        try:
            return quantity.to(target_unit, equivalencies=u.temperature()).value
        except (TypeError, ValueError, UnitConversionError):
            return None

    def _apply_base_mode_temporary_factor(self, operations, profile_unit, temporary_factor):
        factor_operation_index = self._find_base_mode_factor_operation_index(operations, profile_unit)
        if factor_operation_index is None:
            temporary_operation = {
                'operator': '*',
                'source': 'siUnits',
                'type': 'value',
                'value': str(temporary_factor),
            }
            return self._append_after_last_si_unit_operation(operations, temporary_operation)

        updated_operations = [copy.deepcopy(operation) for operation in operations]
        target_operation = updated_operations[factor_operation_index]
        if target_operation.get('operator') == ':':
            if temporary_factor == 0:
                target_operation['value'] = 'nan'
            else:
                target_operation['value'] = str(1 / temporary_factor)
        else:
            target_operation['value'] = str(temporary_factor)
        return updated_operations

    def _find_base_mode_factor_operation_index(self, operations, profile_unit):
        profile_factor = self._to_float(profile_unit.get('conversion_factor'))
        candidate_indexes = []

        for index, operation in enumerate(operations):
            if operation.get('source') != 'siUnits' or operation.get('type') != 'value':
                continue
            if operation.get('operator') not in ('*', ':'):
                continue

            candidate_indexes.append(index)
            operation_value = self._to_float(operation.get('value'))
            if operation_value is None or profile_factor is None:
                continue

            if operation.get('operator') == '*' and self._is_close(operation_value, profile_factor):
                return index
            if (
                operation.get('operator') == ':'
                and profile_factor != 0
                and self._is_close(operation_value, 1 / profile_factor)
            ):
                return index

        return candidate_indexes[-1] if candidate_indexes else None

    def _replace_si_unit_operations(self, operations, replacement_operations):
        before_operations = []
        after_operations = []
        first_si_unit_found = False

        for operation in operations:
            if operation.get('source') == 'siUnits':
                first_si_unit_found = True
                continue

            if first_si_unit_found:
                after_operations.append(copy.deepcopy(operation))
            else:
                before_operations.append(copy.deepcopy(operation))

        replacement = [copy.deepcopy(operation) for operation in replacement_operations]
        if first_si_unit_found:
            return before_operations + replacement + after_operations
        return replacement + before_operations

    @staticmethod
    def _copy_operation_descriptions(operation_descriptions):
        if not operation_descriptions:
            return []
        return [str(description) for description in operation_descriptions]

    @staticmethod
    def _build_prepared_unit_result(operations, descriptions):
        return {
            'operations': operations,
            'descriptions': descriptions,
        }

    @staticmethod
    def _append_auto_correction_descriptions(existing_descriptions, auto_descriptions):
        descriptions = list(existing_descriptions)
        descriptions.extend(auto_descriptions)
        return descriptions

    def _build_base_unit_correction_descriptions(
        self,
        output_table_index,
        axis,
        profile_unit,
        input_unit,
        conversion_factor,
        corrected_operations,
    ):
        return [
            (
                f'[SI Units Auto-Correction] Output Table #{output_table_index} {axis} values were auto-corrected '
                f'because the profile unit "{profile_unit.get("found")}" (UUID {profile_unit.get("uuid")}) '
                f'was not found in the input file. The input unit "{input_unit.get("found")}" with shared base '
                f'unit "{input_unit.get("base_unit")}" is used temporarily instead. The runtime details below '
                f'override the static profile description for this conversion run.'
            ),
            (
                f'[SI Units Auto-Correction] Runtime conversion factor: {conversion_factor}. '
                f'Applied runtime SI operations: {self._summarize_runtime_operations(corrected_operations)}'
            ),
        ]

    def _build_found_unit_correction_descriptions(
        self,
        output_table_index,
        axis,
        profile_unit,
        input_unit,
        corrected_operations,
    ):
        return [
            (
                f'[SI Units Auto-Correction] Output Table #{output_table_index} {axis} values were auto-corrected '
                f'because the profile unit "{profile_unit.get("found")}" (UUID {profile_unit.get("uuid")}) '
                f'was not found in the input file. The input unit "{input_unit.get("found")}" was converted '
                f'temporarily to the profile unit "{profile_unit.get("found")}" via Astropy. The runtime details '
                f'below override the static profile description for this conversion run.'
            ),
            (
                f'[SI Units Auto-Correction] Applied runtime SI operations: '
                f'{self._summarize_runtime_operations(corrected_operations)}'
            ),
        ]

    def _build_failed_unit_correction_descriptions(self, output_table_index, axis, profile_unit):
        return [
            (
                f'[SI Units Auto-Correction] Output Table #{output_table_index} {axis} values could not be '
                f'auto-corrected for profile unit "{profile_unit.get("found")}" (UUID {profile_unit.get("uuid")}). '
                f'No compatible input unit was found for unit mode "{profile_unit.get("unitMode")}".'
            ),
            '[SI Units Auto-Correction] The affected output values are forced to NaN.',
        ]

    @staticmethod
    def _summarize_runtime_operations(operations):
        runtime_parts = []

        for operation in operations:
            if operation.get('source') != 'siUnits' or operation.get('type') != 'value':
                continue
            runtime_parts.append(f'{operation.get("operator")} [Scalar value: {operation.get("value")}]')

        if runtime_parts:
            return ' '.join(runtime_parts)
        return 'No additional runtime SI operation was required.'

    def _append_after_last_si_unit_operation(self, operations, temporary_operation):
        updated_operations = [copy.deepcopy(operation) for operation in operations]
        last_si_unit_index = None

        for index, operation in enumerate(updated_operations):
            if operation.get('source') == 'siUnits':
                last_si_unit_index = index

        if last_si_unit_index is None:
            updated_operations.insert(0, copy.deepcopy(temporary_operation))
        else:
            updated_operations.insert(last_si_unit_index + 1, copy.deepcopy(temporary_operation))

        return updated_operations

    @staticmethod
    def _build_nan_operation():
        return {
            'operator': '*',
            'source': 'siUnits',
            'type': 'value',
            'value': 'nan',
        }

    def _find_preferred_input_unit(self, profile_unit, matcher):
        preferred_index = self._get_profile_data_unit_index(profile_unit.get('uuid'))
        if preferred_index is not None and preferred_index < len(self.input_units):
            preferred_unit = self.input_units[preferred_index]
            if matcher(preferred_unit):
                return preferred_unit

        for index, input_unit in enumerate(self.input_units):
            if index == preferred_index:
                continue
            if matcher(input_unit):
                return input_unit

        return None

    def _get_profile_data_unit_index(self, unit_uuid):
        normalized_uuid = str(unit_uuid) if unit_uuid is not None else None
        if normalized_uuid is None:
            return None

        for index, profile_data_unit in enumerate(self.profile_data_units):
            if str(profile_data_unit.get('uuid')) == normalized_uuid:
                return index
        return None

    def _get_input_unit_by_uuid(self, unit_uuid):
        normalized_uuid = str(unit_uuid) if unit_uuid is not None else None
        if normalized_uuid is None:
            return None

        for input_unit in self.input_units:
            if str(input_unit.get('uuid')) == normalized_uuid:
                return input_unit
        return None

    def _shares_base_unit(self, left_unit, right_unit):
        left_base_unit = self._normalize_unit_text(left_unit.get('base_unit'))
        right_base_unit = self._normalize_unit_text(right_unit.get('base_unit'))
        return bool(left_base_unit) and left_base_unit == right_base_unit

    @staticmethod
    def _normalize_unit_text(value):
        if value is None:
            return ''
        return ' '.join(str(value).split())

    @staticmethod
    def _to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_float(value):
        try:
            return float(str(value).replace(',', '.'))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _is_close(left_value, right_value, tolerance=1e-12):
        return abs(left_value - right_value) <= tolerance


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
            header = os.linesep.join(self.input_tables[table_id]['header']).rstrip()
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

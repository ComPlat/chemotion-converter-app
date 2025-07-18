import copy
import datetime
import logging
import os
import re

from converter_app.models import Profile

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
        self.profile_output_tables = self.profile.data.get('tables', [])
        self.output_tables = []
        self._prepare_identifier()


        for output_table_index, output_table in enumerate(self.profile_output_tables):
            if self._has_loop(output_table_index):
                self._prepare_tables(output_table_index)
            else:
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
        Runs converting process
        :return:
        """
        for output_table_index, output_table in enumerate(self.output_tables):
            header = self._process_prepare_header(output_table)

            self._process_prepare_metadata(header, output_table_index)

            x_column = output_table.get('table', {}).get('xColumn')
            y_column = output_table.get('table', {}).get('yColumn')
            x_operations = output_table.get('table', {}).get('xOperations', [])
            y_operations = output_table.get('table', {}).get('yOperations', [])

            # repare rows
            x_rows = []
            y_rows = []
            for operation in x_operations:
                if operation.get('type') == 'column':
                    operation['rows'] = []
            for operation in y_operations:
                if operation.get('type') == 'column':
                    operation['rows'] = []

            self._process_prepare_data(x_column, x_operations, x_rows, y_column, y_operations, y_rows)

            applied_operators = {
                "applied_x_operator": False,
                "applied_y_operator": False,
                "applied_operator_failed": False,
                "x_operations_description": output_table.get('table', {}).get('xOperationsDescription'),
                "y_operations_description": output_table.get('table', {}).get('yOperationsDescription')
            }
            try:
                for operation in x_operations:
                    applied_operators["applied_x_operator"] |= self._run_operation(x_rows, operation)
                for operation in y_operations:
                    applied_operators["applied_y_operator"] |= self._run_operation(y_rows, operation)
            except CalculationError:
                applied_operators['applied_x_operator'] = applied_operators['applied_y_operator'] = False
                applied_operators['applied_operator_failed'] = True
                x_rows = []
                y_rows = []


            self.tables.append({
                'header': header,
                'x': x_rows,
                'y': y_rows
            } | applied_operators)

    def _process_prepare_data(self, x_column, x_operations, x_rows, y_column, y_operations, y_rows):
        for table_index, table in enumerate(self.input_tables):
            for _, row in enumerate(table['rows']):
                for column_index, _ in enumerate(table['columns']):
                    if x_column and \
                            table_index == x_column.get('tableIndex') and \
                            column_index == x_column.get('columnIndex'):
                        x_rows.append(self.get_value(row, column_index))

                    if y_column and \
                            table_index == y_column.get('tableIndex') and \
                            column_index == y_column.get('columnIndex'):
                        y_rows.append(self.get_value(row, column_index))

                    for operation in x_operations:
                        if operation.get('type') == 'column' and operation.get('column') and \
                                table_index == operation.get('column', {}).get('tableIndex') and \
                                column_index == operation.get('column', {}).get('columnIndex'):
                            operation['rows'].append(self.get_value(row, column_index))

                    for operation in y_operations:
                        if operation.get('type') == 'column' and operation.get('column') and \
                                table_index == operation.get('column', {}).get('tableIndex') and \
                                column_index == operation.get('column', {}).get('columnIndex'):
                            operation['rows'].append(self.get_value(row, column_index))


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
        for profile in Profile.list_including_default(client_id):
            if profile.isDisabled:
                continue
            current_converter = cls(profile, file_data)
            current_matches = current_converter.match()
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

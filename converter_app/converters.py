import copy
import datetime
import logging
import os
import re

from .models import Profile

logger = logging.getLogger(__name__)


class Converter:
    """
    Converter object checks if profile matches to filedata and runs the converting process
    """

    def __init__(self, profile, file_data):
        self.profile = profile
        self.matches = []
        self.tables = []
        self.file_metadata = file_data.get('metadata', {})
        self.input_tables = file_data.get('tables', [])

        if self.profile.data.get('matchTables'):
            self._prepare_identifier()
            self._prepare_tables()
        else:
            self.output_tables = self.profile.data.get('tables', [])
            self.identifiers = self.profile.data.get('identifiers', [])

    def _prepare_tables(self):
        profile_output_tables = self.profile.data.get('tables', [])

        # match the output Table to the input tables and adjust the tableIndexes to the input table
        self.output_tables = []
        for input_table_index, _ in enumerate(self.input_tables):
            output_table = copy.deepcopy(profile_output_tables[0])
            output_table_table = output_table.get('table')
            if output_table_table:
                if 'xColumn' in output_table_table:
                    output_table_table['xColumn']['tableIndex'] = input_table_index
                if 'xColumn' in output_table_table:
                    output_table_table['yColumn']['tableIndex'] = input_table_index
                for x_operation in output_table_table.get('xOperations', []):
                    if 'column' in x_operation:
                        x_operation['column']['tableIndex'] = input_table_index
                for y_operation in output_table_table.get('yOperations', []):
                    if 'column' in y_operation:
                        y_operation['column']['tableIndex'] = input_table_index

            self.output_tables.append(output_table)

    def _prepare_identifier(self):
        profile_identifiers = self.profile.data.get('identifiers', [])
        self.identifiers = []
        for identifier in profile_identifiers:
            if identifier.get('outputTableIndex') is None:
                # if no outputTableIndex was set this identifier is valid for every table
                # no adjustment has to be done
                self.identifiers.append(identifier)
            else:
                # adjust this identifier for every input table
                for input_table_index, _ in enumerate(self.input_tables):
                    # make a copy of the identifier and adjust the outputTableIndex
                    identifier_copy = copy.deepcopy(identifier)
                    identifier_copy['outputTableIndex'] = input_table_index

                    # adjust the (input)tableIndex as well if it was not null
                    if identifier_copy.get('tableIndex') is not None:
                        identifier_copy['tableIndex'] = input_table_index

                    self.identifiers.append(identifier_copy)

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
            header = {}
            for key, value in output_table.get('header', {}).items():
                if isinstance(value, dict):
                    # this is a table identifier, e.g. FIRSTX
                    match = self.match_identifier(value)
                    if match:
                        header[key] = match['value']
                else:
                    header[key] = value

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
                            if operation.get('type') == 'column' and \
                                    table_index == operation.get('column', {}).get('tableIndex') and \
                                    column_index == operation.get('column', {}).get('columnIndex'):
                                operation['rows'].append(self.get_value(row, column_index))

                        for operation in y_operations:
                            if operation.get('type') == 'column' and \
                                    table_index == operation.get('column', {}).get('tableIndex') and \
                                    column_index == operation.get('column', {}).get('columnIndex'):
                                operation['rows'].append(self.get_value(row, column_index))

            for operation in x_operations:
                x_rows = self._run_operation(x_rows, operation)
            for operation in y_operations:
                y_rows = self._run_operation(y_rows, operation)

            self.tables.append({
                'header': header,
                'x': x_rows,
                'y': y_rows
            })

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
                table = 0
                if operation.get('table') is not None:
                    table = int(operation.get('table'))
                try:
                    line_number = int(operation.get('line', ''))
                    header = self.input_tables[table]['header'][line_number - 1].rstrip()
                except (TypeError, ValueError, IndexError):
                    header = os.linesep.join(self.input_tables[table]['header']).rstrip()
                pattern = operation.get('regex')
                if header is not None and pattern is not None:
                    str_value = header
                    match = re.search(pattern, str_value)
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
                if operation.get('operator') in ('+', '-'):
                    op_value = 0
                else:
                    op_value = 1

            if op_value:
                rows[i] = str(self.apply_operation(row, op_value, operation.get('operator')))

        return rows

    def _run_identifier_operation(self, value, operation):
        op_value = operation.get('value')
        if op_value:
            return self.apply_operation(value, op_value, operation.get('operator'))
        else:
            return value

    def apply_operation(self, value, op_value, op_operator):
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
                else:
                    return input_tables[int(index)]
            except KeyError:
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
        for profile in Profile.list(client_id):
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

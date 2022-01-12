import logging
import os
import re
from collections import OrderedDict

from .models import Profile

logger = logging.getLogger(__name__)


class Converter(object):

    def __init__(self, profile):
        self.profile = profile
        self.header = OrderedDict()
        self.match_count = 0

    def match(self, file_data):
        for identifier in self.profile.data.get('identifiers', []):
            if identifier.get('type') == 'metadata':
                value = self.match_metadata(identifier, file_data.get('metadata'))
            elif identifier.get('type') == 'table':
                value = self.match_table(identifier, file_data.get('data'))

            if value is False:
                return False
            else:
                # increment match_count
                self.match_count += 1

                # if a header key is given, store this match in the header
                header_key = identifier.get('headerKey')
                if header_key:
                    self.header[header_key] = value

        # if everything matched, return how many identifiers matched
        return self.match_count

    def match_metadata(self, identifier, metadata):
        metadata_key = identifier.get('metadataKey')
        metadata_value = metadata.get(metadata_key)
        return self.match_value(identifier, metadata_value)

    def match_table(self, identifier, data):
        table_index = identifier.get('tableIndex')
        if table_index is not None:
            try:
                if int(table_index) >= len(data):
                    return False

                table = data[int(table_index)]
            except KeyError:
                return False

            try:
                line_number = int(identifier.get('lineNumber'))
            except (ValueError, TypeError):
                line_number = None

            if line_number is None:
                # use the whole header
                header_value = os.linesep.join(table['header'])
            else:
                try:
                    # the interface counts from 1
                    header_value = table['header'][line_number - 1]
                except IndexError:
                    # the line in the header does not exist
                    return False

            return self.match_value(identifier, header_value.rstrip())

    def match_value(self, identifier, value):
        if value is not None:
            if identifier.get('isRegex'):
                pattern = identifier.get('value')
                match = re.search(pattern, value)
                logger.debug('match_value pattern="%s" value="%s" match=%s', pattern, value, bool(match))
                if match:
                    try:
                        return match.group(1)
                    except IndexError:
                        return match.group(0)
                else:
                    return False
            else:
                result = value == identifier.get('value')
                logger.debug('match_value identifier="%s", value="%s" result=%s', identifier.get('value'), value, result)
                return value if result else False
        else:
            return False

    def get_tables(self, data):
        tables = []
        for table in self.profile.data.get('tables'):
            header = table.get('header', {})
            header.update(self.header)

            x_column = table.get('table', {}).get('xColumn')
            y_column = table.get('table', {}).get('yColumn')
            x_operations = table.get('table', {}).get('xOperations', [])
            y_operations = table.get('table', {}).get('yOperations', [])
            first_row_is_header = self.profile.data.get('firstRowIsHeader')

            # repare rows
            x_rows = []
            y_rows = []
            for operation in x_operations:
                if operation.get('type') == 'column':
                    operation['rows'] = []
            for operation in y_operations:
                if operation.get('type') == 'column':
                    operation['rows'] = []

            for table_index, table in enumerate(data):
                for row_index, row in enumerate(table['rows']):
                    if first_row_is_header and first_row_is_header[table_index] and row_index == 0:
                        pass
                    else:
                        for column_index, column in enumerate(table['columns']):
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
                x_rows = self.run_operation(x_rows, operation)
            for operation in y_operations:
                y_rows = self.run_operation(y_rows, operation)

            tables.append({
                'header': header,
                'x': x_rows,
                'y': y_rows
            })

        return tables

    def run_operation(self, rows, operation):
        for i, row in enumerate(rows):
            op_value = None
            if operation.get('type') == 'column':
                try:
                    op_value = operation['rows'][i]
                except IndexError:
                    pass
            elif operation.get('type') == 'value':
                op_value = operation.get('value')

            if op_value:
                if operation.get('operator') == '+':
                    row_value = float(row) + float(op_value)
                elif operation.get('operator') == '-':
                    row_value = float(row) - float(op_value)
                elif operation.get('operator') == '*':
                    row_value = float(row) * float(op_value)
                elif operation.get('operator') == ':':
                    row_value = float(row) / float(op_value)
                rows[i] = str(row_value)

        return rows

    def get_value(self, row, column_index):
        return str(row[column_index]).replace(',', '.').replace('e', 'E')

    @classmethod
    def match_profile(cls, client_id, file_data):
        converter = None
        matches = 0

        for profile in Profile.list(client_id):
            current_converter = cls(profile)
            current_matches = current_converter.match(file_data)

            logger.info('profile=%s matches=%s', profile.id, current_matches)

            if current_matches is not False and current_matches > matches:
                converter = current_converter
                matches = current_matches

        return converter

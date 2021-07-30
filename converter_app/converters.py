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
                table = data[table_index]
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

            return self.match_value(identifier, header_value)

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
                logger.debug('match_value value="%s" result=%s', value, result)
                return value if result else False
        else:
            return False

    def get_header(self):
        header = self.profile.data.get('header')
        header.update(self.header)

        logger.debug('header=%s', header)
        return header

    def get_data(self, data):
        x_column = self.profile.data.get('table', {}).get('xColumn')
        y_column = self.profile.data.get('table', {}).get('yColumn')
        first_row_is_header = self.profile.data.get('table', {}).get('firstRowIsHeader')

        x = []
        y = []
        for table_index, table in enumerate(data):
            if (x_column and table_index == x_column['tableIndex']) or (y_column and table_index == y_column['tableIndex']):
                for row_index, row in enumerate(table['rows']):
                    if first_row_is_header and first_row_is_header[table_index] and row_index == 0:
                        pass
                    else:
                        for column_index, column in enumerate(table['columns']):
                            if x_column and table_index == x_column['tableIndex'] and column_index == x_column['columnIndex']:
                                x.append(self.get_value(row, column_index))
                            if y_column and table_index == y_column['tableIndex'] and column_index == y_column['columnIndex']:
                                y.append(self.get_value(row, column_index))
        return {
            'x': x,
            'y': y
        }

    def get_value(self, row, column_index):
        return str(row[column_index]).replace(',', '.').replace('e', 'E')

    @classmethod
    def match_profile(cls, file_data):
        converter = None
        matches = 0

        for profile in Profile.list():
            current_converter = cls(profile)
            current_matches = current_converter.match(file_data)

            logger.debug('profile=%s matches=%s', profile.id, current_matches)

            if current_matches is not False and current_matches > matches:
                converter = current_converter
                matches = current_matches

        return converter

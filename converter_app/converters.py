import hashlib
import json
import logging
import os
import re
from pathlib import Path

from flask import current_app as app

logger = logging.getLogger(__name__)


class Converter(object):

    def __init__(self, identifiers, rules):
        self.identifiers = identifiers
        self.rules = self.clean_rules(rules)

    def get_dict(self):
        return {
            'identifiers': self.identifiers,
            'rules': self.rules
        }

    def clean_rules(self, rules):
        cleaned_rules = {}
        for key, value in rules.items():
            if value == 'true':
                value = True
            if value == 'false':
                value = False
            cleaned_rules[key] = value
        return cleaned_rules

    def get_rule(self, rule):
        if rule in self.rules:
            return self.rules.get(rule)

    def save_profile(self):
        profiles_path = Path(app.config['PROFILES_DIR'])
        profiles_path.mkdir(parents=True, exist_ok=True)

        json_data = json.dumps(self.get_dict(), sort_keys=True, indent=4)
        checksum = hashlib.sha1(json_data.encode()).hexdigest()

        file_path = profiles_path / '{}.json'.format(checksum)

        if not file_path.exists():
            with open(file_path, 'w') as fp:
                fp.write(json_data)

    def match(self, file_data):
        for identifier in self.identifiers:
            if identifier.get('type') == 'metadata':
                if not self.match_metadata(identifier, file_data.get('metadata')):
                    return False
            elif identifier.get('type') == 'tabledata':
                if not self.match_data(identifier, file_data.get('data')):
                    return False

        # if everything matched, return True
        return True

    def match_metadata(self, identifier, metadata):
        metadata_key = identifier.get('metadataKey')
        metadata_value = metadata.get(metadata_key)
        return self.match_value(identifier, metadata_value)

    def match_data(self, identifier, data):
        table_index = identifier.get('table')
        if table_index is not None:
            try:
                table = data[table_index]
            except KeyError:
                return False

            try:
                line_number = int(identifier.get('linenumber'))
                header_value = table['header'][line_number]
            except (ValueError, TypeError):
                header_value = os.linesep.join(table['header'])

            return self.match_value(identifier, header_value)

    def match_value(self, identifier, value):
        if value is not None:
            if identifier.get('isExact'):
                result = value == identifier.get('value')
                logger.debug('match_value value="%s" result=%s', value, result)
                return result

            if identifier.get('isRegex'):
                pattern = identifier.get('value')
                match = re.search(pattern, value)
                logger.debug('match_value pattern="%s" value="%s" match=%s', pattern, value, bool(match))
                return bool(match)

    def convert(self, tables):
        x_column = self.get_rule('x_column')
        y_column = self.get_rule('y_column')
        first_row_is_header = self.get_rule('firstRowIsHeader')

        x = []
        y = []
        for table_index, table in enumerate(tables):
            if table_index in [x_column['tableIndex'], y_column['tableIndex']]:
                for row_index, row in enumerate(table['rows']):
                    if first_row_is_header[table_index] and row_index == 0:
                        pass
                    else:
                        for column_index, column in enumerate(table['columns']):
                            if table_index == x_column['tableIndex'] and column_index == x_column['columnIndex']:
                                x.append(row[column_index].replace(',', '.'))
                            if table_index == y_column['tableIndex'] and column_index == y_column['columnIndex']:
                                y.append(row[column_index].replace(',', '.'))

        return {
            'x': x,
            'y': y
        }

    @classmethod
    def match_profile(cls, file_data):
        profiles_path = Path(app.config['PROFILES_DIR'])

        if profiles_path.exists():
            for file_name in os.listdir(profiles_path):
                file_path = profiles_path / file_name

                with open(file_path, 'r') as data_file:
                    data_dict = json.load(data_file)
                    converter = cls(**data_dict)
                    if converter.match(file_data):
                        return converter
        else:
            return None

    @classmethod
    def list_profiles(cls):
        profiles = []
        profiles_path = Path(app.config['PROFILES_DIR'])
        for file_path in Path.iterdir(profiles_path):
            profiles.append(json.loads(file_path.read_text()))
        return profiles

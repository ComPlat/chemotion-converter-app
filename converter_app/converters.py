import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv


class Converter(object):

    def __init__(self, identifiers, rules):
        self.identifiers = identifiers
        self.rules = self.clean_rules(rules)
        self.uuid = str(uuid.uuid4())

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
        profiles_path = Path(os.getenv('PROFILES_PATH', 'profiles'))
        profiles_path.mkdir(parents=True, exist_ok=True)
        os.makedirs(profiles_path, exist_ok=True)
        file_path = profiles_path / '{}.json'.format(self.uuid)
        with open(file_path, 'w') as fp:
            json.dump(self.get_dict(), fp, sort_keys=True, indent=4)

    def apply_to_data(self, tables):
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
                                x.append(row[column_index])
                            if table_index == y_column['tableIndex'] and column_index == y_column['columnIndex']:
                                y.append(row[column_index])

        return {
            'x': x,
            'y': y
        }

    @classmethod
    def match_profile(cls, file_data_metadata):
        profiles_path = Path(os.getenv('PROFILES_PATH', 'profiles'))
        for file_name in os.listdir(profiles_path):
            file_path = profiles_path / file_name

            with open(file_path, 'r') as data_file:
                data_dict = json.load(data_file)
                converter = cls(**data_dict)
                indentifiers = converter.identifiers
                if indentifiers.items() <= file_data_metadata.items():
                    return converter

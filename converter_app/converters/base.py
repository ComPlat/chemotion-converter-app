import os
import json
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
        load_dotenv(Path().cwd() / '.env')
        profiles_dir = os.getenv('PROFILES_DIR')
        os.makedirs(profiles_dir, exist_ok=True)
        file_path = os.path.join(profiles_dir, '{}.json'.format(self.uuid))
        with open(file_path, 'w') as fp:
            json.dump(self.get_dict(), fp, sort_keys=True, indent=4)

    def apply_to_data(self, header, data):
        x_column = self.get_rule('x_column')
        y_column = self.get_rule('y_column')
        first_row_is_header = self.get_rule('firstRowIsHeader')
        points = []
        if not first_row_is_header:
            x = None
            y = None
            for entry in header:
                if entry['key'] == x_column:
                    x = entry['name']
                if entry['key'] == y_column:
                    y = entry['name']
            if x and y:
                points.append([x, y])
        for row in data:
            x_value = row.get(x_column)
            y_value = row.get(y_column)
            points.append([x_value, y_value])
        return {'points': points}


import json
import logging
import uuid
from collections import defaultdict
from pathlib import Path
from jsonschema import validate, exceptions

import magic
from flask import current_app

from .utils import check_uuid, reader_json_shema

logger = logging.getLogger(__name__)


class Profile(object):

    def __init__(self, profile_data, client_id, profile_id=None):
        self.data = profile_data
        self.client_id = client_id
        self.id = profile_id

    def clean(self):
        self.errors = defaultdict(list)

        if self.id is None and 'id' in self.data:
            profile_id = self.data['id']
            if check_uuid(profile_id):
                existing_profile = Profile.retrieve(self.client_id, self.data['id'])
                if existing_profile:
                    self.errors['id'].append('A profile with this ID already exists.')
            else:
                self.errors['id'].append('id is not a valid UUID4.')

        if 'identifiers' in self.data:
            if isinstance(self.data['identifiers'], list):
                pass
            else:
                self.errors['identifiers'].append('identifiers has to be a list.')
        else:
            self.errors['identifiers'].append('identifiers have to be provided.')

        if 'tables' in self.data:
            if isinstance(self.data['tables'], list):
                for table in self.data['tables']:
                    if 'table' in table:
                        if isinstance(table['table'], dict):
                            pass
                        else:
                            self.errors['tables'].append('table.table has to be an object.')
                    else:
                        self.errors['table'].append('table.table has to be provided.')

                    if 'header' in table:
                        if isinstance(table['header'], dict):
                            pass
                        else:
                            self.errors['tables'].append('table.header field has to be an object.')
                    else:
                        self.errors['header'].append('table.header has to be provided.')
            else:
                self.errors['tables'].append('tables have to be provided.')

        if not self.errors:
            return True

    def save(self):
        profiles_path = Path(current_app.config['PROFILES_DIR']).joinpath(self.client_id)
        profiles_path.mkdir(parents=True, exist_ok=True)

        if self.id is None:
            if 'id' in self.data:
                self.id = self.data['id']
            else:
                # create a uuid for new profiles
                self.id = str(uuid.uuid4())

        file_path = profiles_path.joinpath(self.id).with_suffix('.json')
        with open(file_path, 'w') as fp:
            json.dump(self.data, fp, sort_keys=True, indent=4)

    def delete(self):
        profiles_path = Path(current_app.config['PROFILES_DIR']).joinpath(self.client_id)

        file_path = profiles_path.joinpath(self.id).with_suffix('.json')
        if file_path.is_file():
            file_path.unlink()

    @property
    def as_dict(self):
        return {
            'id': self.id,
            **self.data
        }

    @classmethod
    def load(cls, file_path):
        profile_data = json.loads(file_path.read_text())

        # ensure compatibility with older isRegex flag
        for identifier in profile_data.get('identifiers', []):
            if 'match' not in identifier:
                if 'isRegex' in identifier:
                    identifier['match'] = ('regex' if identifier['isRegex'] else 'exact')
                    del identifier['isRegex']
                else:
                    identifier['match'] = 'exact'

        return profile_data

    @classmethod
    def list(cls, client_id):
        profiles_path = Path(current_app.config['PROFILES_DIR']).joinpath(client_id)

        if profiles_path.exists():
            for file_path in Path.iterdir(profiles_path):
                profile_id = str(file_path.with_suffix('').name)
                profile_data = cls.load(file_path)
                yield cls(profile_data, client_id, profile_id)
        else:
            return []

    @classmethod
    def retrieve(cls, client_id, profile_id):
        profiles_path = Path(current_app.config['PROFILES_DIR']).joinpath(client_id)

        # make sure that its really a uuid, this should prevent file system traversal
        if check_uuid(profile_id):
            file_path = profiles_path.joinpath(profile_id).with_suffix('.json')
            if file_path.is_file():
                profile_data = cls.load(file_path)
                return cls(profile_data, client_id, profile_id)

        return False


class Reader(object):

    def __init__(self, reader_data, client_id, reader_id=None):
        self.data = reader_data
        self.client_id = client_id
        self.id = reader_id or reader_data.get('id')

    def clean(self):
        self.errors = defaultdict(list)

        if self.id is not None and check_uuid(self.id):
            existing_profile = Reader.retrieve(self.client_id, self.id)
            if not existing_profile:
                self.errors['id'].append('A profile with this ID already exists.')
        else:
            self.errors['id'].append('id is not a valid UUID4.')

        try:
            validate(instance=self.data, schema=reader_json_shema())
        except exceptions.ValidationError as ex:
            self.errors[ex.json_path].append(ex.message)

        if not self.errors:
            return True

    def save(self):
        profiles_path = Path(current_app.config['READERS_DIR']).joinpath(self.client_id)
        profiles_path.mkdir(parents=True, exist_ok=True)

        if self.id is None:
            if 'id' in self.data:
                self.id = self.data['id']
            else:
                # create a uuid for new profiles
                self.id = str(uuid.uuid4())

        file_path = profiles_path.joinpath(self.id).with_suffix('.json')
        with open(file_path, 'w') as fp:
            json.dump(self.data, fp, sort_keys=True, indent=4)

    def delete(self):
        profiles_path = Path(current_app.config['READERS_DIR']).joinpath(self.client_id)

        file_path = profiles_path.joinpath(self.id).with_suffix('.json')
        if file_path.is_file():
            file_path.unlink()

    @property
    def as_dict(self):
        return {
            'id': self.id,
            **self.data
        }

    @classmethod
    def create(cls, reader_data, client_id):

        def create_identifier():
            return {
                "match": "exact",
                "optional": False,
                "show": True,
                "type": "global",
                "value": ""
            }

        reader_data['identifiers'] = {'meta': {}, 'content': []}
        reader_data['tables'] = []
        reader_data['commend'] = {
            'line_commend': create_identifier(),
            'multi_line_commend_end': create_identifier(),
            'multi_line_commend_start': create_identifier()
        }
        reader_data['delimiters'] = {
            'ignore_within_quotes': True,
            'table_delimiters': [],
            'options': [
                {
                    'name': 'semicolon',
                    'active': True,
                    'symbol': ';'
                },
                {
                    'name': 'comma',
                    'active': True,
                    'symbol': ','
                },
                {
                    'name': 'tab',
                    'active': True,
                    'symbol': '\t'
                },
                {
                    'name': 'space',
                    'active': False,
                    'symbol': ' '
                },
                {
                    'name': 'equals',
                    'active': True,
                    'symbol': '='
                },
                {
                    'name': 'own',
                    'active': False,
                    'symbol': ''
                }
            ],
            'free_identifier': create_identifier(),
        }

        return cls(reader_data, client_id)

    @classmethod
    def load(cls, file_path):
        profile_data = json.loads(file_path.read_text())

        # ensure compatibility with older isRegex flag
        # for identifier in profile_data.get('identifiers', []):
        #    if 'match' not in identifier:
        #        if 'isRegex' in identifier:
        #            identifier['match'] = ('regex' if identifier['isRegex'] else 'exact')
        #            del identifier['isRegex']
        #        else:
        #            identifier['match'] = 'exact'

        return profile_data

    @classmethod
    def list(cls, client_id):
        readers_path = Path(current_app.config['READERS_DIR']).joinpath(client_id)

        if readers_path.exists():
            for file_path in Path.iterdir(readers_path):
                profile_id = str(file_path.with_suffix('').name)
                profile_data = cls.load(file_path)
                yield cls(profile_data, client_id, profile_id)
        else:
            return []

    @classmethod
    def retrieve(cls, client_id, profile_id):
        profiles_path = Path(current_app.config['READERS_DIR']).joinpath(client_id)

        # make sure that its really a uuid, this should prevent file system traversal
        if check_uuid(profile_id):
            file_path = profiles_path.joinpath(profile_id).with_suffix('.json')
            if file_path.is_file():
                profile_data = cls.load(file_path)
                return cls(profile_data, client_id, profile_id)

        return False


class File(object):

    def __init__(self, file):
        self.fp = file
        self.name = file.filename
        self.content_type = file.content_type

        # read the file
        self.content = file.read()
        file.seek(0)

        self.mime_type = magic.Magic(mime=True).from_buffer(self.content)
        self.encoding = magic.Magic(mime_encoding=True).from_buffer(self.content)
        self.suffix = Path(self.name).suffix

        # decode file string
        self.string = self.content.decode(self.encoding) if self.encoding != 'binary' else None

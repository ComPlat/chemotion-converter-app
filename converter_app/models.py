import json
import logging
import uuid
from collections import defaultdict
from pathlib import Path

from flask import current_app

logger = logging.getLogger(__name__)


class Profile(object):

    def __init__(self, profile_data, client_id, profile_id=None):
        self.data = profile_data
        self.client_id = client_id
        self.id = profile_id

    def clean(self):
        self.errors = defaultdict(list)
        if 'identifiers' in self.data:
            if isinstance(self.data['identifiers'], list):
                pass
            else:
                self.errors['identifiers'].append('This field has to be a list.')
        else:
            self.errors['identifiers'].append('This field has to be provided.')

        if 'table' in self.data:
            if isinstance(self.data['table'], dict):
                pass
            else:
                self.errors['table'].append('This field has to be an object.')
        else:
            self.errors['table'].append('This field has to be provided.')

        if 'header' in self.data:
            if isinstance(self.data['header'], dict):
                pass
            else:
                self.errors['header'].append('This field has to be an object.')
        else:
            self.errors['header'].append('This field has to be provided.')

        if not self.errors:
            return True

    def save(self):
        profiles_path = Path(current_app.config['PROFILES_DIR']).joinpath(self.client_id)
        profiles_path.mkdir(parents=True, exist_ok=True)

        if self.id is None:
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
    def list(cls, client_id):
        profiles_path = Path(current_app.config['PROFILES_DIR']).joinpath(client_id)

        if profiles_path.exists():
            for file_path in Path.iterdir(profiles_path):
                profile_id = str(file_path.with_suffix('').name)
                profile_data = json.loads(file_path.read_text())
                yield cls(profile_data, client_id, profile_id)
        else:
            return []

    @classmethod
    def retrieve(cls, client_id, profile_id):
        profiles_path = Path(current_app.config['PROFILES_DIR']).joinpath(client_id)

        # make sure that its really a uuid, this should prevent file system traversal
        try:
            uuid.UUID(profile_id, version=4)
        except ValueError:
            return False

        file_path = profiles_path.joinpath(profile_id).with_suffix('.json')
        if file_path.is_file():
            profile_data = json.loads(file_path.read_text())
            return cls(profile_data, client_id, profile_id)
        else:
            return False

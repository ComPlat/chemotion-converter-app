import json
import os
import tempfile
import uuid

from flask import jsonify


class Reader(object):

    def check(self):
        raise NotImplementedError

    def process(self):
        data_dict = self.convert_to_dict()
        data_dict_with_metadata = self.add_metadata(data_dict)
        self.save_to_tempfile(data_dict_with_metadata)
        return data_dict_with_metadata

    def convert_to_dict(self):
        raise NotImplementedError

    def add_metadata(self, data_dict):
        data_dict['metadata'] = {
            'file_name': self.file_name,
            'content_type': self.content_type,
            'extension': self.extension,
            'uuid': self.uuid
        }
        return data_dict

    def save_to_tempfile(self, data_json):
        tempdir = tempfile.gettempdir()
        path = os.path.join(tempdir)
        with open(path + '/{}.json'.format(self.uuid), 'a') as jsonfile:
            json.dump(data_json, jsonfile)

    def __init__(self, file):
        self.file = file
        self.extension = ''
        self.content_type = self.file.content_type
        self.file_name = file.filename
        self.uuid = str(uuid.uuid4())

        if '.' in self.file_name:
            file_name_splitted = self.file_name.split('.')
            self.extension = file_name_splitted[-1]
            self.file_name = file_name_splitted[0]

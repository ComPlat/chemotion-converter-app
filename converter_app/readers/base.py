import json
import os
import tempfile
from datetime import datetime

from flask import jsonify


class Reader(object):

    def check(self):
        raise NotImplementedError

    def process(self):
        data_dict = self.convert_to_dict()
        data_dict_with_props = self.add_properties(data_dict)
        self.save_to_tempfile(data_dict_with_props)
        return jsonify({'result': data_dict_with_props}), 201

    def convert_to_dict(self):
        raise NotImplementedError

    def add_properties(self, data_dict):
        data_dict['properties'] = {
            'file_name': self.file_name,
            'content_type': self.content_type,
            'extension': self.extension,
            'time_stamp': self.time_stamp
        }
        return data_dict

    def save_to_tempfile(self, data_json):
        tempdir = tempfile.gettempdir()
        path = os.path.join(tempdir)
        with open(path + '/{}.json'.format(self.time_stamp), 'a') as jsonfile:
            json.dump(data_json, jsonfile)

    def __init__(self, file):
        self.file = file
        self.extension = ''
        self.content_type = self.file.content_type
        self.file_name = file.filename
        self.time_stamp = datetime.now().strftime('%Y%m%d%H%M%S')

        if '.' in self.file_name:
            file_name_splitted = self.file_name.split('.')
            self.extension = file_name_splitted[-1]
            self.file_name = file_name_splitted[0]

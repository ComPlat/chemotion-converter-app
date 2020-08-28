import json
import logging
import os
import tempfile
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)


class Reader(object):

    def __init__(self, file_reader, file_name, content_type):
        self.file_reader = file_reader
        self.file_name = file_name
        self.content_type = content_type
        self.extension = Path(file_name).suffix
        self.uuid = str(uuid.uuid4())

    def check(self):
        raise NotImplementedError

    def process(self):
        data_dict = {
            'data': self.get_data(),
            'metadata': self.get_metadata()
        }

        self.save_to_tempfile(data_dict)
        return data_dict

    def get_data(self):
        raise NotImplementedError

    def get_metadata(self):
        return {
            'file_name': self.file_name,
            'content_type': self.content_type,
            'extension': self.extension,
            'uuid': self.uuid
        }

    def save_to_tempfile(self, data_json):
        tempdir = tempfile.gettempdir()
        path = os.path.join(tempdir)
        with open(path + '/{}.json'.format(self.uuid), 'a') as jsonfile:
            json.dump(data_json, jsonfile)

    def peek_ascii(self):
        file_string = self.file_reader.peek(1024)
        encoding = None

        for item in ['utf-8', 'iso-8859-1']:
            try:
                file_string = file_string.decode(item)
                encoding = item
                break
            except UnicodeDecodeError:
                pass

        logger.debug('encoding=%s', encoding)
        return file_string, encoding

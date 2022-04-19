import logging
from pathlib import Path

import magic

logger = logging.getLogger(__name__)


class Reader(object):

    def __init__(self, file, file_name, content_type):
        self.file = file
        self.file_name = file_name
        self.content_type = content_type

        self.file_content = self.file.read()
        self.file.seek(0)

        self.mime_type = magic.Magic(mime=True).from_buffer(self.file_content)
        self.encoding = magic.Magic(mime_encoding=True).from_buffer(self.file_content)

        self.extension = Path(file_name).suffix

    def check(self):
        raise NotImplementedError

    def process(self):
        return {
            'tables': self.get_tables(),
            'metadata': self.get_metadata()
        }

    def get_tables(self):
        raise NotImplementedError

    def get_metadata(self):
        return {
            'file_name': self.file_name,
            'content_type': self.content_type,
            'mime_type': self.mime_type,
            'extension': self.extension,
            'reader': self.__class__.__name__
        }

    def append_table(self, tables):
        table = {
            'header': [],
            'metadata': {},
            'columns': [],
            'rows': []
        }
        tables.append(table)
        return table

    def get_value(self, value):
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            return value

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class Reader(object):

    float_pattern = re.compile(r'(-?\d+[,.]*\d*[eE+\-\d]*)\S*')
    float_de_pattern = re.compile(r'(-?[\d.]+,\d*[eE+\-\d]*)')
    float_us_pattern = re.compile(r'(-?[\d,]+.\d*[eE+\-\d]*)')

    def __init__(self, file):
        self.file = file

    @property
    def as_dict(self):
        return {
            'tables': self.tables,
            'metadata': self.metadata
        }

    def check(self):
        raise NotImplementedError

    def process(self):
        self.tables = self.get_tables()
        self.metadata = self.get_metadata()

    def get_tables(self):
        raise NotImplementedError

    def get_metadata(self):
        return {
            'file_name': self.file.name,
            'content_type': self.file.content_type,
            'mime_type': self.file.mime_type,
            'extension': self.file.suffix,
            'reader': self.__class__.__name__,
            'uploaded': datetime.utcnow().isoformat()
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

    def get_shape(self, row):
        shape = []
        for cell in row:
            value = cell.strip()
            if value in self.empty_values:
                shape.append('')
            elif self.float_pattern.match(value):
                shape.append('f')
            else:
                shape.append('s')

        return shape

    def get_value(self, value):
        if self.float_de_pattern.match(value):
            # remove any digit group seperators and replace the comma with a period
            return value.replace('.', '').replace(',', '.')
        if self.float_us_pattern.match(value):
            # just remove the digit group seperators
            return value.replace(',', '')
        else:
            return value

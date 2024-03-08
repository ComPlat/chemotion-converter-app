import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class Table(dict):
    """
    Table class represents on table converter
    """

    def __init__(self):
        super().__init__({
            'header': [],
            'metadata': MetadataContainer({}),
            'columns': [],
            'rows': []
        })

    def __add__(self, other):
        raise NotImplementedError


class MetadataContainer(dict[str:any]):
    """
    Metadata container extents dict ´. It extents the dict class by add_unique.
    """

    def add_unique(self, key: str, value: any):
        """
        Checks if key exists. If so it extends the key with an integer. This integer ingresses until the key is not
        a key in the dict.
        :param key: dict key
        :param value: Value
        """
        o_key = key
        idx = 1
        while key in self:
            key = f"{o_key} ({idx})"
            idx += 1
        self[key] = value


class Reader:
    """
    Base reader. Any reader needs to extend this abstract reader.
    """
    float_pattern = re.compile(r'(-?\d+[,.]*\d*[eE+\-\d]*)\S*')
    float_de_pattern = re.compile(r'(-?[\d.]+,\d*[eE+\-\d]*)')
    float_us_pattern = re.compile(r'(-?[\d,]+.\d*[eE+\-\d]*)')

    def __init__(self, file):
        self.empty_values = ['', 'n.a.']
        self.identifier = None
        self.metadata = None
        self.tables = None
        self.file = file

    @property
    def as_dict(self):
        """
        Returns all values as dict: {tables: [...], metadata: {...}}
        """
        return {
            'tables': self.tables,
            'metadata': self.metadata
        }

    def check(self):
        """
        Abstract method check if the reader matches a file
        :return: [bool] true if the Reader checks a file
        """
        raise NotImplementedError

    def process(self):
        """
        Processes a file and stores all converted values in self.tables and self.metadata
        """
        self.tables = self.get_tables()
        self.metadata = self.get_metadata()

    def validate(self):
        """

        :return:
        """
        for table_index, table in enumerate(self.tables):
            for key, value in table['metadata'].items():
                if not isinstance(value, str):
                    class_name = type(value).__name__
                    logger.warning(
                        'metadata Table #%d %s="%s" is not of type str, but %s (%s)', table_index, key, value,
                        class_name, self.identifier)

        for key, value in self.metadata.items():
            if not isinstance(value, str):
                class_name = type(value).__name__
                logger.warning('metadata %s="%s" is not of type str, but %s (%s)', key, value, class_name,
                               self.identifier)

    def get_tables(self) -> list[Table]:
        """
        method converts the content of a file.
        """
        tables = self.prepare_tables()
        for table in tables:
            if len(table['rows']) > 0:
                start_len_c = len(table['columns'])
                should_len_c = len(table['rows'][0])
                if table['rows'] and start_len_c != should_len_c:
                    max_key = max(-1, 0, *[int(x['key']) for x in table['columns']])
                    table['columns'] += [{
                        'key': f'{idx + max_key}',
                        'name': f'Column #{idx + start_len_c}'
                    } for idx, value in enumerate(table['rows'][0][start_len_c:])]
                    table['columns'] = sorted(table['columns'], key=lambda x: int(x['key']))
                for k,v in enumerate(table['columns'][:should_len_c]):
                    v['key'] = f'{k}'

            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))
        return tables

    def prepare_tables(self) -> list[Table]:
        """
        Abstract method converts the content of a file.
        """
        raise NotImplementedError

    def get_metadata(self):
        """
        Returns a metadata collection object.
        :return: dict {file_name: ...,  content_type: ..., mime_type: ..., extension: ..., reader: ..., uploaded: ...}
        """
        return {
            'file_name': self.file.name,
            'content_type': self.file.content_type or '',
            'mime_type': self.file.mime_type,
            'extension': self.file.suffix,
            'reader': self.__class__.__name__,
            'uploaded': datetime.utcnow().isoformat()
        }

    def append_table(self, tables: list) -> Table:
        """
        Adds a new Table to the table list
        :param tables: a list of all tables
        :return: Table
        """
        table = Table()
        tables.append(table)
        return table

    def get_shape(self, row) -> list:
        """
        Returns encoded shape of a row
        :param row: list
        :return: shape
        """
        shape = []
        for cell in row:
            if cell is None:
                shape.append(None)
            else:
                cell = str(cell).strip()
                if cell in self.empty_values:
                    shape.append('')
                elif self.float_pattern.match(cell):
                    shape.append('f')
                else:
                    shape.append('s')

        return shape

    def get_value(self, value: str) -> str:
        """
        Checks if values is a stringified float and makes it to a standard.
        :param value: Sting value
        :return: The argument as standard float if necessary
        """
        if self.float_de_pattern.match(value):
            # remove any digit group seperators and replace the comma with a period
            return value.replace('.', '').replace(',', '.')
        if self.float_us_pattern.match(value):
            # just remove the digit group seperators
            return value.replace(',', '')

        return value

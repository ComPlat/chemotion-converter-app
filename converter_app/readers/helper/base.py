import logging
import os
import re
from datetime import datetime, UTC

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

    def add_metadata(self, key, value):
        """
        Add metadata to table
        :param key: Key of the metadata
        :param value: Value of the metadata
        :return:
        """
        self['metadata'].add_unique(key, value)

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

    Attributes:
        identifier (str): The manufacturer of the car.
        metadata (dict): Auto generated bsed on the convertion results.
        tables (int): Auto generated bsed on the convertion results.
        file (converter_app.modelsFile): Received File from the client (Chemotion)
        file_content ([]converter_app.modelsFile): file_content contains all files archived in the 'file' if it is a tarball file.
        is_tar_ball (bool): Ture if 'file' is a tarball file.
    """

    float_pattern = re.compile(r'[-+]?[0-9]*[.,]?[0-9]+(?:[eE][-+]?[0-9]+)?\s*')
    int_pattern = re.compile(r'[+-]?\d+')
    float_de_pattern = re.compile(r'(-?[\d.]+,\d*[eE+\-\d]*)')
    float_us_pattern = re.compile(r'(-?[\d,]+.\d*[eE+\-\d]*)')
    float_on_zeros = re.compile(r'.0*$')

    identifier = None
    priority = 100

    def __init__(self, file, *tar_content):
        self._empty_values = ['', 'n.a.']
        self.metadata = None
        self.tables = None
        self.file = file
        self.file_content = tar_content
        self.is_tar_ball = len(tar_content) > 0

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
        Abstract method check if the reader matches a filelist
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
                for k, v in enumerate(table['columns'][:should_len_c]):
                    v['key'] = f'{k}'

            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))
            # Necessary: dictionary changed size during iteration
            keys_vals = list(table['metadata'].items())
            for key, value in keys_vals:
                if isinstance(value, str):
                    origin_val = table['metadata'][key]
                    new_val = self._get_value_as_decimal(value)
                    if origin_val != new_val:
                        table['metadata'][key] = new_val

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
            'file_name': os.path.basename(self.file.name),
            'content_type': self.file.content_type or '',
            'mime_type': self.file.mime_type,
            'extension': self.file.suffix,
            'reader': self.__class__.__name__,
            'uploaded': datetime.now(UTC).isoformat()
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
                if isinstance(cell, datetime):
                    shape.append('f')
                    continue
                cell = str(cell).strip()
                if cell in self._empty_values:
                    shape.append('')
                elif self.float_pattern.fullmatch(cell):
                    shape.append('f')
                else:
                    shape.append('s')

        return shape

    def as_number(self, value: str) -> float | int:
        """
        Returns a numeric value if possible:

        :raises ValueError: If not convertable
        :param value: as string
        :return: numeric value either int or float
        """
        if self.int_pattern.fullmatch(value) is not None:
            return int(value)
        return float(self.get_value(value))

    def get_value(self, value: str) -> str:
        """
        Checks if values is a stringified float and makes it to a standard.
        :param value: Sting value
        :return: The argument as standard float if necessary
        """
        return self._get_value(value)

    def _get_value_as_decimal(self, value: str) -> any:
        if value is None:
            return value
        val = self._get_value(str(value))
        if self.float_pattern.fullmatch(val) is not None and 'e' in value.lower() and ',' in value.lower():
            return val
        return value

    def _get_value(self, value: str) -> str:
        """
        Checks if values is a stringified float and makes it to a standard.
        :param value: Sting value
        :return: The argument as standard float if necessary
        """
        if isinstance(value, str) and self.float_pattern.fullmatch(value):
            if self.float_de_pattern.match(value):
                # remove any digit group seperators and replace the comma with a period
                return value.replace('.', '').replace(',', '.')
            if self.float_us_pattern.match(value):
                # just remove the digit group seperators
                return value.replace(',', '')

        return str(value)

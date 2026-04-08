import logging
import os
import re
from datetime import datetime, UTC

from converter_app.readers.helper.unit_finder import StdUnits, UnitFinder, UnitRule

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
        self.units = []
        self.std_units = self._copy_std_units()
        self._configure_std_units()
        self.unit_finder = UnitFinder(custom_unit_map=self.std_units, ignore_dimless=True)

    @property
    def as_dict(self):
        """
        Returns all values as dict: {tables: [...], metadata: {...}}
        """
        return {
            'tables': self.tables,
            'metadata': self.metadata,
            'units': self.units
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
        self.apply_unit_finder()
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

    def _copy_std_units(self) -> dict[str, UnitRule]:
        """
        Return a reader-local copy of the shared standard unit definitions.
        """
        return dict(StdUnits)

    def _configure_std_units(self) -> None:
        """
        Hook for child readers to extend or override the local standard unit map.

        This method is called during reader initialization after a reader-local copy
        of ``StdUnits`` has been created. Changes made here affect only the current
        reader instance and do not modify the shared global defaults for other
        readers.

        Child readers should use ``_set_std_unit(...)`` for single entries or
        ``_extend_std_units(...)`` for multiple entries.

        Example:
            A child reader can define its own interpretation for a unit label such
            as ``kWh`` and map it to a custom target base unit:

            ```python
            from astropy import units as u

            class DtaReader(Reader):
                def _configure_std_units(self) -> None:
                    self._set_std_unit("kWh", u.kW * u.h, u.W * u.s)
            ```

        In that example:
        - ``found`` stays ``"kWh"``
        - ``source_unit`` is interpreted as ``u.kW * u.h``
        - ``base_unit`` is forced to ``u.W * u.s``
        - the conversion factor is calculated automatically by Astropy (and
          ``from astropy import units as u``)

        This is the recommended place for reader-specific unit aliases, overrides,
        and custom base-unit mappings.
        """
        return None

    def _set_std_unit(
        self,
        unit_text: str,
        source_unit: str | object,
        base_unit: str | object | None = None,
        conversion_factor: float | None = None,
    ) -> None:
        """
        Add or override a unit rule for the current reader instance only.
        """
        finder = UnitFinder()
        normalized_unit_text = finder.normalize_text(unit_text)
        normalized_source_unit = finder._to_unit(source_unit)
        normalized_base_unit = finder._to_unit(base_unit) if base_unit is not None else None
        self.std_units[normalized_unit_text] = UnitRule(
            source_unit=normalized_source_unit,
            base_unit=normalized_base_unit,
            conversion_factor=conversion_factor,
        )
        if hasattr(self, 'unit_finder'):
            self.unit_finder.add_custom_unit(
                normalized_unit_text,
                normalized_source_unit,
                normalized_base_unit,
                conversion_factor,
            )

    def _extend_std_units(self, unit_map: dict[str, UnitRule]) -> None:
        """
        Extend the reader-local standard unit map with multiple entries.
        """
        for unit_text, rule in unit_map.items():
            self._set_std_unit(
                unit_text,
                rule.source_unit,
                rule.base_unit,
                rule.conversion_factor,
            )

    def get_table_unit_values(self, table: Table) -> list[str]:
        """
        Return strings that should be scanned for units for one table.
        """
        return [str(value) for value in table.get('header', [])]

    def apply_unit_finder(self) -> None:
        """
        Apply unit detection to all tables and store the results in table metadata
        and in the reader-level ``self.units`` list.
        """
        self.units = []
        seen_unit_ids = set()

        for table in self.tables or []:
            unit_values = self.get_table_unit_values(table)
            if not unit_values:
                continue

            unit_results = self.unit_finder.find_units(unit_values)
            self.unit_finder.found_units_to_options_list()

            for index, unit_result in enumerate(unit_results):
                table['metadata'][f'unit_{index:02d}_found'] = str(unit_result['found'])
                table['metadata'][f'unit_{index:02d}_conversion_factor'] = str(unit_result['conversion_factor'])
                table['metadata'][f'unit_{index:02d}_base_unit'] = str(unit_result['base_unit'])

                unit_id = str(unit_result['uuid'])
                if unit_id in seen_unit_ids:
                    continue

                seen_unit_ids.add(unit_id)
                self.units.append({
                    'found': str(unit_result['found']),
                    'conversion_factor': str(unit_result['conversion_factor']),
                    'base_unit': str(unit_result['base_unit']),
                    'uuid': unit_id,
                })

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

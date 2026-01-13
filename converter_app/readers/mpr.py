import json
import logging
import tempfile

import yadg
from yadg.extractors.eclab.techniques import param_map  # needs yagd version > 6.0.2

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)

if not any(x[1] == 2 for x in param_map["Set I/C"]):
    param_map["Set I/C"] += ("UNKNWON", 2),  # guess


class MprReader(Reader):
    """
    Implementation of the MPR Reader. It extends converter_app.readers.helper.base.Reader
    MPS is a binary file format. This reader uses the https://github.com/dgbowl/yadg
    """

    identifier = 'mpr_reader'
    priority = 10

    def __init__(self, file):
        super().__init__(file)
        self._numpy_data = None

    def check(self):
        """
        :return: True if it fits
        """
        check_result = self.file.encoding == 'binary' and self.file.suffix == '.mpr'
        if check_result:
            with tempfile.NamedTemporaryFile() as tp:
                try:
                    tp.write(self.file.content)
                    result = yadg.extractors.extract(filetype="eclab.mpr", path=tp.name)
                    self._numpy_data = result.to_dict()
                except (NotImplementedError, AssertionError, ValueError) as e:
                    return False
        return check_result

    def _append_table(self, tables, table_name):
        table = self.append_table(tables)
        table['metadata'].add_unique('___TABLE_NAME__', table_name)
        return table

    def prepare_tables(self):
        """
        Converts numpy-like extracted data from YADG into Chemotion-compatible tables.
        If a 'cycle number' column exists, split the data by cycle into separate tables.
        """
        tables = []

        for key, numpy_value in self._numpy_data.items():
            base_table = self._append_table(tables, key)
            dict_value = numpy_value.to_dict()
            self._convert_attrs(dict_value, base_table)

            # Prepare table structure
            for _ in range(list(dict_value['dims'].values())[0]):
                base_table['rows'].append([])

            # Fill coordinate and data variables
            self._convert_data_table(dict_value, base_table, 'coords')
            self._convert_data_table(dict_value, base_table, 'data_vars')

            # Handle potential cycle-based split
            self._split_by_cycle(base_table, tables, key)

        return tables

    def _convert_data_table(self, dict_value, table, value_name):
        if value_name in dict_value:
            for k, v in dict_value[value_name].items():
                units = v.get('attrs', {}).get('units')
                if units is not None:
                    table['metadata'].add_unique(f'unit.{value_name}.{k}', str(units))
                    units = f' ({units})'
                else:
                    units = ''

                table['columns'].append({
                    'key': str(len(table['columns'])),
                    'name': str(v.get('attrs', {}).get('standard_name', k)) + units
                })

                for i, row in enumerate(table['rows']):
                    row.append(v.get('data')[i])

    def _convert_attrs(self, dict_value, table):
        if 'attrs' in dict_value:
            attrs = dict_value.get('attrs')
            attrs = json.loads(attrs.get('original_metadata', '{}'))
            self._handle_metadata(attrs, table, 'settings')
            self._handle_metadata(attrs, table, 'log')
            self._handle_metadata(attrs, table, 'params')

    def _handle_metadata(self, attrs, table, man_key):
        for k, v in attrs.get(man_key, {}).items():
            if isinstance(v, list):
                for i, lv in enumerate(v):
                    table['metadata'].add_unique(f'{man_key}.{k}.{i}', str(lv))
            elif isinstance(v, dict):
                for i, lv in v.keys():
                    table['metadata'].add_unique(f'{man_key}.{k}.{i}', str(lv))
            else:
                table['metadata'].add_unique(f'{man_key}.{k}', str(v))

    def _split_by_cycle(self, base_table: dict, tables: list, table_name: str) -> None:
        """
        Splits the given base_table into multiple tables by 'cycle number' column
        if that column exists. Each resulting table is appended to 'tables'.

        :param base_table: The table containing all rows before splitting
        :param tables: The global list of tables to append to
        :param table_name: Name of the original dataset (used for naming new tables)
        """
        # Extract column names and check if 'cycle number' exists
        column_names = [col['name'] for col in base_table['columns']]
        if 'cycle number' not in column_names:
            # No cycle column → keep table as-is
            # tables.append(base_table)
            return

        cycle_idx = column_names.index('cycle number')

        # Group rows by cycle number
        cycle_groups = {}
        for row in base_table['rows']:
            cycle_value = row[cycle_idx]
            cycle_groups.setdefault(cycle_value, []).append(row)

        # Create new tables per cycle
        for cycle_value, rows in sorted(cycle_groups.items(), key=lambda x: x[0]):
            cycle_table = self._append_table(tables, f"{table_name}_cycle_{cycle_value}")
            cycle_table['columns'] = list(base_table['columns'])  # Copy columns
            cycle_table['rows'] = rows
            cycle_table['metadata'].add_unique('cycle_number', str(cycle_value))


Readers.instance().register(MprReader)

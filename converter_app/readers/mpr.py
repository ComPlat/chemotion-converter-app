import json
import logging
import tempfile
import yadg
from yadg.extractors.eclab.techniques import param_map  # needs yagd version > 6.0.2

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)

if not any(x[1] == 2 for x in param_map["set_I/C"]):
     param_map["set_I/C"] += ("UNKNWON", 2),  # guess


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
        tables = []

        for k, numpy_value in self._numpy_data.items():
            table = self._append_table(tables, k)
            dict_value = numpy_value.to_dict()
            self._convert_attrs(dict_value, table)

            for _ in range(list(dict_value['dims'].values())[0]):
                table['rows'].append([])
            self._convert_data_table(dict_value, table, 'coords')
            self._convert_data_table(dict_value, table, 'data_vars')


        return tables

    def _convert_data_table(self, dict_value, table, value_name):
        if value_name in dict_value:
            for k,v in dict_value[value_name].items():
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
            for param in attrs.get('params', []):
                self._handle_metadata({'params': param}, table, 'params')

    def _handle_metadata(self, attrs, table, man_key):
        for k, v in attrs.get(man_key, {}).items():
            table['metadata'].add_unique(f'{man_key}.{k}', str(v))


Readers.instance().register(MprReader)

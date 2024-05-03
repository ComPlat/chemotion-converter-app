import json
import logging
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class JsonReader(Reader):
    """
    Implementation of the Json Reader. It is a basic json file reader
    """
    identifier = 'json_reader'
    priority = 100
    _all_tables = {}
    table = None

    def check(self):
        """
        :return: True if it fits
        """
        return self.file.suffix.lower() == '.json'

    def _rec_reader(self, elem, key):
        if isinstance(elem, dict):
            iterator = elem.items()
        elif isinstance(elem, list):
            if all(isinstance(x, (int, float)) for x in elem):
                if len(elem) not in self._all_tables:
                    self._all_tables[len(elem)] = {}
                self._all_tables[len(elem)][key] = elem
                return
            iterator = enumerate(elem)
        else:
            self.table['metadata'].add_unique(key, elem)
            return
        for k, v in iterator:
            temp_key = f'{key}.{k}'
            self._rec_reader(v, temp_key)

    def prepare_tables(self):
        """
        Parse the json File. For all metadata information the parser uses the json path as key with "." separation.
        All arrays of number will be columns of tables. The system will check for all columns of same length
        and combine them to table.
        example:
        From :
        {
            "a": "VAL A",
            "b": {
                "a": "VAL B.A"
            },
            data: {
             "X": [1,2,3,4],
             "Y": [0.1,0.2,0.3,0.4],
             "X1": [1,2,3],
             "Y2": [0.1,0.2,0.3]
            }
        }

        metadata =>
        #.a = Val A
        #.b.a = VAL B.A
        data =>
        Table 1 => [
            #.data.X - [1,2,3,4],
            #.data.Y - [0.1,0.2,0.3,0.4]
        ]
        Table 2 => [
            #.data.X1 - [1,2,3],
            #.data.Y1 - [0.1,0.2,0.3]
        ]
        :return:
        """
        tables = []
        self.table = self.append_table(tables)
        as_dict = json.loads(self.file.content)
        self._rec_reader(as_dict, '#')

        for table_len, table_col in self._all_tables.items():
            table = self.append_table(tables)
            table['rows'] = [[] for x in range(table_len)]
            table['columns'] = []
            idx = 0
            for k, values in table_col.items():
                table['columns'].append({
                    'key': str(idx),
                    'name': f'{k}'
                })
                idx += 1
                for i, v in enumerate(values):
                    table['rows'][i].append(v)

        return tables


Readers.instance().register(JsonReader)

import logging

import xml.etree.ElementTree as ET

from converter_app.models import File
from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)


class XMLReader(Reader):
    """
    Reader for XML files.
    """

    identifier = 'xml_reader'
    priority = 10

    def __init__(self, file: File):
        super().__init__(file)
        self._file_extensions = ['.xml']
        self._table = None
        self._data_tables = []
        self._potential_data_tables = {}

    def check(self):
        return self.file.suffix.lower() in self._file_extensions

    def _get_tag_name(self, node:  ET.Element):
        return node.tag.split('}', 1)[-1]


    def _filter_data_rows(self, node:  ET.Element, text: str, xml_path: str) -> bool:
        text_array = [x for x in text.strip().split(' ') if x != '']
        shape = self.get_shape(text_array)
        if all(x == 'f' for x in shape) and len(shape) > 1:
            self._data_tables.append(self._generate_data_table(shape, xml_path, text_array, node))
            return True
        return False

    def _generate_data_table(self, shape: list[str], xml_path: str, text_array: list[str], node: ET.Element):
        return {
            'shape': ''.join(shape),
            'path': xml_path,
            'values': [self.as_number(x) for x in text_array],
            'node': node
        }

    def _handle_node(self, node:  ET.Element, xml_path: str, node_name: str):
        pass

    def _add_metadata(self, key: str, val: any, node: ET.Element):
        m = self.float_pattern.fullmatch(val)
        if key in self._potential_data_tables:
            if m and  self._potential_data_tables[key] is not None:
                self._potential_data_tables[key]['values'].append(self.as_number(val))
            else:
                self._potential_data_tables[key] = None
        elif m:
            self._potential_data_tables[key] = self._generate_data_table(['f'], key, [val], node)
        self._table.add_metadata(key, val)

    def _read_node(self, node: ET.Element, xml_path: str = '#'):
        for child in node:
            text = child.text

            try:
                local_name = self._get_tag_name(child)
                new_path = f'{xml_path}.{local_name}'
            except ValueError:
                new_path = 'Unknown'
                local_name = ''

            self._handle_node(child, xml_path, local_name)

            if text is not None and not self._filter_data_rows(child, text, new_path):
                self._add_metadata(new_path, text.strip(), node)
            for k, v in child.attrib.items():
                self._add_metadata(f'{new_path}.{k}', v, node)

            self._read_node(child, new_path)

    def prepare_tables(self):
        tables = []
        # xml_str = re.sub(r'\sxmlns\s*([:=])', r' xmlns_removed\g<1>', self.file.string)
        self._table = self.append_table(tables)
        root = ET.XML(self.file.content)
        # self._read_node(root)
        # root = etree.XML(self.file.content)

        # Remove unused namespace declarations
        # ET.cleanup_namespaces(root)

        self._read_node(root)

        current_shape = ''
        for table_col in self._data_tables:
            if current_shape != table_col['shape']:
                current_shape = table_col['shape']
                self._table = self.append_table(tables)
                self._table['rows'] = [[] for x in range(len(table_col['values']))]

            tag_name =  self._get_tag_name(table_col['node'])
            self._table.add_metadata(f"COL #{len(self._table['rows'][0])}", tag_name)
            self._table.add_metadata(f"COL #{len(self._table['rows'][0])} XML PATH", table_col['path'])

            for i, v in enumerate(table_col['values']):
                self._table['rows'][i].append(v)

            for k, v in table_col['node'].attrib.items():
                self._table.add_metadata(f'{tag_name}.{k}', v)

        return tables


Readers.instance().register(XMLReader)

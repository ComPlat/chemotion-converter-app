import logging
import xml.etree.ElementTree as ET

from converter_app.models import File
from converter_app.readers.helper.base import Reader, MetadataContainer
from converter_app.readers.helper.reader import Readers

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
        self._potential_data_tables = MetadataContainer({})

    def check(self):
        return self.file.suffix.lower() in self._file_extensions

    def _get_tag_name(self, node: ET.Element):
        return node.tag.split('}', 1)[-1]

    def _filter_data_rows(self, node: ET.Element, text: str, xml_path: str) -> bool:
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

    def handle_node(self, node: ET.Element, xml_path: str, node_name: str):
        """
        This method can be overridden to handle special nodes separately.

        :param node: XML node Object
        :param xml_path: Path in global XML-file to this node
        :param node_name: Name of the Node
        """
        pass

    def ignore_node(self, node: ET.Element, xml_path: str, node_name: str) -> bool:
        """
        This method check if a note can be ignored (after it was handled).

        :param node: XML node Object
        :param xml_path: Path in global XML-file to this node
        :param node_name: Name of the Node#
        :returns: true if note should be ignored
        """
        return False

    def _add_metadata(self, key: str, val: any, node: ET.Element):
        m = self.float_pattern.fullmatch(val)
        if key in self._potential_data_tables:
            if m and self._potential_data_tables[key] is not None:
                self._potential_data_tables[key]['values'].append(self.as_number(val))
                self._potential_data_tables[key]['shape'] += 'f'
            else:
                self._potential_data_tables[key] = None
        elif m:
            self._potential_data_tables.add_unique(key, self._generate_data_table(['f'], key, [val], node))
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

            self.handle_node(child, xml_path, local_name)
            if not self.ignore_node(child, xml_path, local_name):
                if text is not None and not self._filter_data_rows(child, text, new_path):
                    self._add_metadata(new_path, text.strip(), node)
                for k, v in child.attrib.items():
                    self._add_metadata(f'{new_path}.{k}', v, node)

            self._read_node(child, new_path)

    def prepare_tables(self):
        tables = []
        self._table = self.append_table(tables)
        root = ET.XML(self.file.content)
        self._read_node(root)
        self._merge_tables(self._data_tables, tables)

        potential_tables = [x for k, x in self._potential_data_tables.items() if
                            x is not None and len(x.get('values', [])) > 1]
        potential_tables.sort(key=lambda x: len(x['values']))
        self._merge_tables(potential_tables, tables)

        return tables

    def _merge_tables(self, data_tables: list, tables):
        current_shape = ''
        for table_col in data_tables:
            if current_shape != table_col['shape']:
                current_shape = table_col['shape']
                self._table = self.append_table(tables)
                self._table['rows'] = [[] for x in range(len(table_col['values']))]

            tag_name = self._get_tag_name(table_col['node'])
            self._table.add_metadata(f"COL #{len(self._table['rows'][0])}", tag_name)
            self._table.add_metadata(f"COL #{len(self._table['rows'][0])} XML PATH", table_col['path'])

            for i, v in enumerate(table_col['values']):
                self._table['rows'][i].append(v)

            self._read_node(table_col['node'])

            #for k, v in table_col['node'].attrib.items():
            #    self._table.add_metadata(f'{tag_name}.{k}', v)


Readers.instance().register(XMLReader)

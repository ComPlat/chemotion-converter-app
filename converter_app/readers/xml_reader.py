import logging

from lxml import etree

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
        self._step_sizes = {}

    def check(self):
        return self.file.suffix.lower() in self._file_extensions

    def _filter_data_rows(self, node: etree._Element, text: str, xml_path: str) -> bool:
        text_array = [x for x in text.strip().split(' ') if x != '']
        shape = self.get_shape(text_array)
        if all(x == 'f' for x in shape) and len(shape) > 1:
            self._data_tables.append({
                'shape': ''.join(shape),
                'path': xml_path,
                'values': [self.as_number(x) for x in text_array],
                'node': node
            })
            return True
        return False

    def _read_node(self, node: etree._Element, xml_path: str = '#'):
        for child in node:
            text = child.text

            try:
                local_name = etree.QName(child).localname
                new_path = f'{xml_path}.{local_name}'
            except ValueError:
                new_path = 'Unknown'
                local_name = ''

            try:
                if local_name in ['endPosition', 'startPosition']:
                    pos_path = '.'.join(xml_path.split('.')[:-1])
                    if pos_path not in self._step_sizes:
                        self._step_sizes[pos_path] = {}
                    self._step_sizes[pos_path][local_name] = self.as_number(text)
            except ValueError:
                pass

            if text is not None and not self._filter_data_rows(node, text, new_path):
                self._table.add_metadata(new_path, text.strip())
            for k, v in child.attrib.items():
                self._table.add_metadata(f'{new_path}.{k}', v)

            self._read_node(child, new_path)

    def prepare_tables(self):
        tables = []
        # xml_str = re.sub(r'\sxmlns\s*([:=])', r' xmlns_removed\g<1>', self.file.string)
        self._table = self.append_table(tables)
        root = etree.fromstring(self.file.string)

        # Remove unused namespace declarations
        etree.cleanup_namespaces(root)

        self._read_node(root)

        current_shape = ''
        for table_col in self._data_tables:
            if current_shape != table_col['shape']:
                current_shape = table_col['shape']
                self._table = self.append_table(tables)
                self._table['rows'] = [[] for x in range(len(table_col['values']))]

            tag_name = etree.QName(table_col['node']).localname
            self._table.add_metadata(f"ROW #{len(self._table['rows'][0])}", tag_name)
            self._table.add_metadata(f"ROW #{len(self._table['rows'][0])} XML PATH", table_col['path'])

            for i, v in enumerate(table_col['values']):
                self._table['rows'][i].append(v)

            for path, values in self._step_sizes.items():
                if table_col['path'].startswith(path) and 'endPosition' in values and 'startPosition' in values:
                    v = (values['endPosition'] - values['startPosition']) / len(self._table['rows'])
                    self._table.add_metadata(f'{path}.stepSize', v)
                    self._table.add_metadata(f'{path}.startPosition', values['startPosition'])
                    self._table.add_metadata(f'{path}.endPosition', values['endPosition'])

            for k, v in table_col['node'].attrib.items():
                self._table.add_metadata(f'{tag_name}.{k}', v)

        return tables


Readers.instance().register(XMLReader)

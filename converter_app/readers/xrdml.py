import xml.etree.ElementTree as ET

from converter_app.models import File
from converter_app.readers.helper.reader import Readers
from converter_app.readers.xml_reader import XMLReader


class XRDMLReader(XMLReader):
    """
    Reader for XRDML files. Powder diffraction from Bruker
    """

    identifier = 'xrdml_reader'

    def __init__(self, file: File, *tar_content):
        super().__init__(file, *tar_content)
        self._file_extensions = ['.xrdml']
        self._step_sizes = {}

    def handle_node(self, node: ET.Element, xml_path: str, node_name: str):

        try:
            if node_name == 'positions':
                if xml_path not in self._step_sizes:
                    self._step_sizes[xml_path] = []
                self._step_sizes[xml_path].append({
                    'axis': node.attrib.get('axis', '-'),
                    'unit': node.attrib.get('unit', '-'),
                })
                for child in node:
                    if child.tag.endswith('startPosition'):
                        self._step_sizes[xml_path][-1]['startPosition'] = self.as_number(child.text.strip())
                    if child.tag.endswith('endPosition'):
                        self._step_sizes[xml_path][-1]['endPosition'] = self.as_number(child.text.strip())
        except ValueError:
            pass

    def _prepare_step_size(self, col_length, table):
        for i in range(col_length):
            mt_p = table['metadata'][f"COL #{i} XML PATH"]
            for path, values in self._step_sizes.items():
                if mt_p.startswith(path):
                    for v in values:
                        if 'endPosition' in v and 'startPosition' in v:
                            step_size = (v['endPosition'] - v['startPosition']) / (len(table['rows']) - 1)
                            table.add_metadata(f'COL #{col_length}.stepSize', step_size)
                            table.add_metadata(f'COL #{col_length}.startPosition', v['startPosition'])
                            table.add_metadata(f'COL #{col_length}.endPosition', v['endPosition'])
                            table.add_metadata(f'COL #{col_length}.unit', v['unit'])
                            table.add_metadata(f'COL #{col_length}.axis', v['axis'])
                            col_length += 1

    def prepare_tables(self):
        tables = super().prepare_tables()
        for table in tables:
            row_length = len(table['rows'])
            if row_length > 0:
                col_length = len(table['rows'][0])
                self._prepare_step_size(col_length, table)

        return tables

Readers.instance().register(XRDMLReader)

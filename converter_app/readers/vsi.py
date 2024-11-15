import logging

import xml.etree.ElementTree as ET

from converter_app.models import File
from converter_app.readers.helper.reader import Readers
from converter_app.readers.xml_reader import XMLReader

logger = logging.getLogger(__name__)


class VsiReader(XMLReader):
    """
        Implementation of the Vsm Reader. It extends converter_app.readers.XMLReader
    """
    identifier = 'vsi_reader'
    priority = 8

    def __init__(self, file: File):
        super().__init__(file)
        self.data_key = ''

    def check(self):
        if not super().check():
            return False
        return self.file.string.find('<![CDATA[')

    def handle_node(self, node: ET.Element, xml_path: str, node_name: str):
        """
        This method can be overridden to handle special nodes separately.

        :param node: XML node Object
        :param xml_path: Path in global XML-file to this node
        :param node_name: Name of the Node
        """
        if node_name == 'Data':
            if node.text.strip() == '':
                if node.attrib.get('typename') == 'FixedSpacing2D':
                    self.data_key = node.attrib.get('key')
                else:
                    value, unit = self.get_value_with_unit(node)
                    self._table['metadata'][node.attrib.get('key')] = value + unit
            else:
                self._table['metadata'][node.attrib.get('key')] = node.text

        if node_name in ('Dim1Spacing','Dim2Spacing'):
            value, unit = self.get_value_with_unit(node)
            self._table['metadata'][self.data_key + '.' + node_name] = value + unit

    def get_value_with_unit(self, node):
        """
        This method handles Value + Unit sub notes

        :param node: XML node Object
        :returns: value and unit if available
        """
        try:
            value = node.find('Value').text.strip()
        except AttributeError:
            value = ''
        try:
            unit = ' ' + node.find('Unit').text.strip()
        except AttributeError:
            unit = ''
        return value, unit

    def ignore_node(self, node: ET.Element, xml_path: str, node_name: str) -> bool:
        """
        This method check if a note can be ignored (after it was handled).

        :param node: XML node Object
        :param xml_path: Path in global XML-file to this node
        :param node_name: Name of the Node#
        :returns: true if note should be ignored
        """
        return node_name in ('DataContainer', 'Data', 'Unit', 'Value', 'Dim1Spacing','Dim2Spacing')


    def prepare_tables(self):
        tables = []
        table = super().prepare_tables()[0]
        tables.append(table)

        table['metadata'].pop('Matrix', None)

        return tables


Readers.instance().register(VsiReader)

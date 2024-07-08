from converter_app.models import File
from converter_app.readers.xml_reader import XMLReader
from converter_app.readers.helper.reader import Readers


class XRDMLReader(XMLReader):
    """
    Reader for XRDML files. Powder diffraction from Bruker
    """

    identifier = 'xrdml_reader'

    def __init__(self, file: File):
        super().__init__(file)
        self._file_extensions = ['.xrdml']


Readers.instance().register(XRDMLReader)

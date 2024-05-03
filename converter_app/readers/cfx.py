import logging
from converter_app.readers.cif import CifReader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class CfxReader(CifReader):
    """
    CFX reader reads cfx_lana files a slim version of cfx files
    """
    identifier = 'cfx_reader'
    file_prefix = '.cfx_lana'
    priority = 11


Readers.instance().register(CfxReader)

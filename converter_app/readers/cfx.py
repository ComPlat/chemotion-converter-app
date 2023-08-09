import logging
from .cif import CifReader

logger = logging.getLogger(__name__)

class CfxReader(CifReader):
    identifier = 'cfx_reader'
    file_prefix = '.cfx_lana'
    priority = 11
import logging

import openlab as ol

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)

class LcmsReader(Reader):
    """
    Reads tarballed lcms files / folders with extension .tar.gz
    """
    identifier = 'lcms_reader'
    priority = 4

    def __init__(self, file, *tar_files):
        super().__init__(file, *tar_files)
        self.df = None
        self.temp_dir = None

    def check(self):
        """
        :return: True if it fits
        """

        if self.is_tar_ball:
            try:
                if len(self.file_content) > 1:
                    self.df = ol.read_ms(self.file_content[0].file_path)
                else:
                    return False
                return True
            except ValueError:
                pass
        return False

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        """
        table['columns'] = [{
            'key': str(idx),
            'name': f'{value}'
        } for idx, value in enumerate(['Time', 'Wavelength'])]
        """

        return tables

Readers.instance().register(LcmsReader)

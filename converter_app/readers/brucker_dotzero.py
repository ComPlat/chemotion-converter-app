import logging
import os
import tempfile

import opusFC

from converter_app.readers import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)


class DotZeroReader(Reader):
    """
    Reads .0 files using the package: https://github.com/qedsoftware/brukeropusreader
    """
    identifier = 'dot_zero_reader'
    priority = 79

    def __init__(self, file, *tar_files):
        super().__init__(file, *tar_files)
        self._dotzero_file = None
        self._dx_name = None
        self._has_temp_copy = False

    def check(self):
        """
        :return: True if it fits
        """

        dotzero_extentions = ['.0']

        if self.is_tar_ball:
            for x in self.file_content:
                try:
                    if opusFC.isOpusFile(x.fp.filename):
                        self._dotzero_file = x.fp.filename
                        return True
                except (ValueError, TypeError, FileNotFoundError):
                    pass

            dx_file = next((x for x in self.file_content if x.suffix.lower() == '.dx'), None)
            if dx_file is not None:
                self._dx_name = dx_file.name[:-3]
        elif self.file.suffix.lower() in dotzero_extentions:
            with tempfile.NamedTemporaryFile(suffix='.0', delete=False) as temp_file:
                self._dotzero_file = temp_file.name  # You can now access the file path
                self.file.fp.save(self._dotzero_file)
                self._has_temp_copy = True
                if opusFC.isOpusFile(self._dotzero_file):
                    return True
                return False

        return self._dotzero_file is not None

    def __del__(self):
        if  self._has_temp_copy:
            os.remove(self._dotzero_file)

    def prepare_tables(self):
        tables = []

        dbs = opusFC.listContents(self._dotzero_file)  # List all data blocks in the file
        for block in dbs:
            table = self.append_table(tables)
            data = opusFC.getOpusData( self._dotzero_file, block)  # Retrieve data from the specific block
            for x in block:
                table.add_metadata('__BLOCK__', str(x))

            for key, value in data.parameters.items():
                table.add_metadata(str(key), str(value))

            table['rows'] = [[float(val), float(data.y[i])] for i, val in enumerate(data.x)]
            table['columns'] = [{
                        'key': f'{idx}',
                        'name': name
                    } for idx, name in enumerate(['X', 'Y'])]

        return tables


Readers.instance().register(DotZeroReader)

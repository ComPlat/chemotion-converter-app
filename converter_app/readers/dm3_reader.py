import logging
import os

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

import dm3_lib as dm3
import tempfile

logger = logging.getLogger(__name__)

class DM3Reader(Reader):
    """
    Reads metadata from dm3 file images
    """
    identifier = 'dm3_reader'
    priority = 50

    def _ensure_str(self, x):
        return x.decode() if isinstance(x, bytes) else x

    def check(self):
        if self.file.suffix.lower() == '.dm3':
            return True
        return False

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        file = self.file.content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dm3") as tmp:
            tmp.write(file)
            tmp_path = tmp.name

        dm3f = dm3.DM3(tmp_path)
        table['metadata'] = {self._ensure_str(k): self._ensure_str(v) for k, v in dm3f.info.items()}

        os.remove(tmp_path)


        return tables


Readers.instance().register(DM3Reader)
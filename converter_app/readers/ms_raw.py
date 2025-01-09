import logging

import requests
from flask import current_app

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.asc_helper import AscHelper

logger = logging.getLogger(__name__)


class MsRawReader(Reader):
    """
    Reader uses MS raw files using the MS_CONVERTER
    """
    identifier = 'ms_raw_reader'
    priority = 10

    def __init__(self, file):
        super().__init__(file)

    # two or more chars in row

    def check(self):
        """
        :return: True if it fits
        """
        result = False

        if self.file.suffix.lower() == '.raw' and self.file.encoding == 'binary':
            parsed_url = current_app.config.get('MS_CONVERTER')
            files = {
                "main_file": (self.file.name, self.file.content, "image/x-panasonic-rw")
            }

            res = requests.post(parsed_url + 'msconvert_conversion', data={'test':''}, files=files, timeout=60)
            if res.status_code == 200:
                return True

        return result

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        return tables


Readers.instance().register(MsRawReader)

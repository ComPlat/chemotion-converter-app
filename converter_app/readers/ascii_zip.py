import logging
import re

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers
from converter_app.readers.ascii import AsciiReader

logger = logging.getLogger(__name__)


class AsciiReaderArchive(Reader):
    """
    Implementation of the Ascii Reader. It extends converter_app.readers.helper.base.Reader
    """
    identifier = 'ascii_reader_archive'
    priority = 10001

    # two or more chars in row
    text_pattern = re.compile(r'[A-Za-z]{2,}')

    def check(self):
        """
        :return: True if it fits
        """

        return self.is_tar_ball

    def prepare_tables(self):
        tables = []
        for current_file in [self.file] + list(self.file_content):
            ar = AsciiReader(current_file)
            if ar.check():
                tables += ar.prepare_tables()

        return tables


Readers.instance().register(AsciiReaderArchive)

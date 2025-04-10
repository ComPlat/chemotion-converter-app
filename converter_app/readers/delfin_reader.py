import logging
import re

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class DelfinReader(Reader):
    identifier = 'deflin_reader'
    priority = 3

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self.lines = None

    def _parse_input(self):
        current_header = '[NO HEADER]'
        header_re = re.compile(r'^\[.+]$')
        content = {current_header: []}
        for x in self.file.string.splitlines():
            if x != '':
                if header_re.match(x) is not None:
                    current_header = x
                    content[x] = []
                else:
                    content[current_header].append(x)
        return content

    def check(self):
        """
        :return: True if it fits
        """
        result = self.file.suffix.lower() == '.txt'
        if result:
            self.lines = self._parse_input()
            result = any("DELFIN" in line for line in self.lines.get('[NO HEADER]', []))
        return result

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        table['metadata'] = {"test": "test"}
        return tables

Readers.instance().register(DelfinReader)
import logging

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class JascoReader(Reader):
    """
    Reading rasco files
    """
    identifier = 'jasco_reader'
    priority = 99

    def __init__(self, file):
        super().__init__(file)
        self.lines = None
        self.header_length = 8

    def check(self):
        """
        :return: True if it fits
        """
        result = False
        if self.file.string is not None:
            if len(self.file.string.splitlines()) == 1:
                file_lines = self.file.string.split(',')
                if len(file_lines) > self.header_length - 1 and file_lines[self.header_length - 1] == str(
                        len(file_lines) - self.header_length):
                    result = True
                    self.lines = file_lines

        logger.debug('result=%s', result)
        return result

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        for i, line in enumerate(self.lines):
            if i < self.header_length:
                table['header'].append(line)
            else:
                x, y = line.split()
                table['rows'].append((self.get_value(x), self.get_value(y)))

        return tables


Readers.instance().register(JascoReader)

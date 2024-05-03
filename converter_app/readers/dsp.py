import logging
from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)


class DSPReader(Reader):
    """
    Reads .dsp files
    """
    identifier = 'dsp_reader'
    priority = 95

    def check(self):
        """
        :return: True if it fits
        """
        if self.file.suffix.lower() == '.dsp' and self.file.mime_type == 'text/plain':
            first_line = self.file.string.splitlines()[0]
            return 'sinacsa' in first_line

        return False

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        header = True

        for line in self.file.fp.readlines():
            row = line.decode(self.file.encoding).rstrip()

            if header:
                table['header'].append(row)
            elif row:
                table['rows'].append([self.get_value(row)])

            if row == '#DATA':
                # this is where the data starts
                header = False

        return tables


Readers.instance().register(DSPReader)

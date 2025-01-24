import logging
import re

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class AsciiReader(Reader):
    """
    Implementation of the Ascii Reader. It extends converter_app.readers.helper.base.Reader
    """
    identifier = 'ascii_reader'
    priority = 1000

    # two or more chars in row
    text_pattern = re.compile(r'[A-Za-z]{2,}')

    def check(self):
        """
        :return: True if it fits
        """
        return not self.file.encoding == 'binary'

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        # loop over lines of the file
        previous_count = None
        for line in self.file.fp.readlines():
            row = line.decode(self.file.encoding).rstrip()
            count = None

            # try to match text for the header
            text_match = self.text_pattern.search(row)
            if text_match:
                if table['rows']:
                    # if a table is already there, this must be a new header
                    table = self.append_table(tables)

                # append header line to last table
                table['header'].append(row)
            else:
                # try to match columns of floats
                row = row.replace('n.a.', '')
                float_match = self.float_pattern.findall(row)
                if float_match:
                    float_match = [self.get_value(float_str.strip()) for float_str in float_match]
                    count = len(float_match)

                    if table['rows'] and count != previous_count:
                        # start a new table if the shape has changed
                        table = self.append_table(tables)

                    table['rows'].append(float_match)
                else:
                    if table['rows']:
                        # if a table is already there, this must be a new header
                        table = self.append_table(tables)

                    table['header'].append(row)

            previous_count = count

        return tables


Readers.instance().register(AsciiReader)

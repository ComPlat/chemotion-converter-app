import logging
import re

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.unit_finder import UnitFinder

logger = logging.getLogger(__name__)


class AsciiReader(Reader):
    """
    Implementation of the Ascii Reader. It extends converter_app.readers.helper.base.Reader
    """
    identifier = 'ascii_reader'
    priority = 1000

    # two or more chars in row
    text_pattern = re.compile(r'[A-Za-z]{2,}')

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self.unit_finder = UnitFinder(ignore_dimless=True)
        self.unit_finder.add_custom_unit('unix seconds', 's')
        self.unit_finder.add_custom_unit('Time (unix seconds)', 's')

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

        for table in tables:
            self.add_unit_metadata(table)

        return tables

    def add_unit_metadata(self, table):
        """
        Scan table header strings for units and store the result in table metadata.
        """
        unit_results = self.unit_finder.find_units(table['header'])
        self.unit_finder.found_units_to_options_list()
        for index, unit_result in enumerate(unit_results):
            table['metadata'][f'unit_{index:02d}_found'] = str(unit_result['found'])
            table['metadata'][f'unit_{index:02d}_conversion_factor'] = str(unit_result['conversion_factor'])
            table['metadata'][f'unit_{index:02d}_base_unit'] = str(unit_result['base_unit'])
            self.units.append({'found' : str(unit_result['found']), 'conversion_factor' : str(unit_result['conversion_factor']), 'base_unit' : str(unit_result['base_unit'])})


Readers.instance().register(AsciiReader)

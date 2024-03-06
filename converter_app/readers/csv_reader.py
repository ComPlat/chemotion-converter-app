import csv
import io
import logging

from converter_app.readers.helper import get_shape
from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)


class CSVReader(Reader):
    """
    Reads and fixes CSV files into metadata and data tables
    """
    identifier = 'csv_reader'
    priority = 100

    def __init__(self, file):
        super().__init__(file)
        self.lines = None
        self.rows = None

        self.empty_values = ['', 'n.a.']
        self.table_min_rows = 20
        self.delimiters = {
            '\t': 'tab',
            ';': 'semicolon',
            ',': 'comma',
        }
        self.lineterminators = {
            '\r\n': '\\r\\n',
            '\r': '\\r',
            '\n': '\\n',
        }
        self.sniff_buffer_size = 100000

    def check(self):
        # check using seperate function for inheritance
        result = self.check_csv()
        if result:
            self.lines = self.file.string.splitlines()
            try:
                self.rows = list(csv.reader(io.StringIO(self.file.string), self.file.features('csv_dialect')))
            except:
                self.rows = list(csv.reader(self.lines, self.file.features('csv_dialect')))

        logger.debug('result=%s', result)
        return result

    def check_csv(self):
        """
        Checks if file is CSV readable
        :return: True if is CSV readable
        """
        try:
            # check if the csv dialect was already found
            self.file.features('csv_dialect')
            return True
        except AttributeError:
            if self.file.string is not None:
                # check different delimiters one by one
                for delimiter in self.delimiters.keys():
                    try:
                        self.file.set_features('csv_dialect',
                                               csv.Sniffer().sniff(self.file.string[:self.sniff_buffer_size],
                                                                   delimiters=delimiter))
                        return True
                    except csv.Error:
                        pass

        return False

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        # loop over rows and sort into blocks of similar shape
        blocks = []
        block = {}
        for index, row in enumerate(self.rows):
            shape = get_shape(row)
            if block.get('shape') is None or not self.compare_shape(shape, block.get('shape', [])):
                block = {'indexes': [], 'shape': shape}
                blocks.append(block)

            block['indexes'].append(index)

        # loop over blocks and sort into header, table, and metadata
        prev_block = None
        for block in blocks:
            if len(block['indexes']) < self.table_min_rows or not block['shape']:
                # this is the header
                if table['rows']:
                    # if a table is already there, this must be a new header
                    table = self.append_table(tables)

                table['header'] += [self.lines[index] for index in block['indexes']]
            else:
                # this is the table
                if not table['rows']:
                    # if there are no tables, we can try to find the columns previous line
                    if prev_block is not None:
                        this_row = self.rows[block['indexes'][0]]
                        prev_row = self.rows[prev_block['indexes'][-1]]

                        if len(prev_row) > 0 and len(prev_row) <= len(this_row):
                            # add the column names as metadata
                            table['metadata'] = {
                                f'column_{idx:02d}': str(value) for idx, value in enumerate(prev_row)
                            }
                            # remove the colum line from the header
                            table['header'] = table['header'][:-1]

                table['rows'] += [[self.get_value(value) for value in self.rows[index]] for index in block['indexes']]

            prev_block = block

        # build columns
        for table in tables:
            table['columns'] = []
            if table['rows']:
                for idx in range(len(table['rows'][0])):
                    name = table['metadata'].get(f'column_{idx:02d}')
                    table['columns'].append({
                        'key': str(idx),
                        'name': f'Column #{idx} ({name})' if name else f'Column #{idx}'
                    })

        return tables

    def get_metadata(self):
        csv_dialect = self.file.features('csv_dialect')
        metadata = super().get_metadata()
        metadata['lineterminator'] = self.lineterminators.get(csv_dialect.lineterminator, csv_dialect.lineterminator)
        metadata['quoting'] = str(csv_dialect.quoting)
        metadata['doublequote'] = str(csv_dialect.doublequote)
        metadata['delimiter'] = self.delimiters.get(csv_dialect.delimiter, csv_dialect.delimiter)
        metadata['quotechar'] = csv_dialect.quotechar
        metadata['skipinitialspace'] = str(csv_dialect.skipinitialspace)
        return metadata

    def compare_shape(self, shape_a, shape_b):
        """
        this function compares two shapes, shapes are considered equal if
        floats or strings are at the same positions, spaces are considered wildcards
        since they could be both floats or strings
        :param shape_a: encoded line/row shape
        :param shape_b: encoded line/row shape
        :return: True if shape_a equals shape_b
        """
        if shape_a == shape_b:
            # both shapes are identical
            return True

        if len(shape_a) != len(shape_b):
            # shapes have different length
            return False

        if not any(shape_a):
            # shape_a consits only of spaces
            return False

        if not any(shape_b):
            # shape_b consits only of spaces
            return False

        for a, b in zip(shape_a, shape_b):
            if a and b and a != b:
                # cell a is not equal cell b or one of the two is empty
                return False

        return True


Readers.instance().register(CSVReader)

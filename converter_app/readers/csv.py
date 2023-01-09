import csv
import io
import logging

from .base import Reader

logger = logging.getLogger(__name__)


class CSVReader(Reader):
    identifier = 'csv_reader'
    priority = 100

    empty_values = ['', 'n.a.']
    table_min_rows = 20
    delimiters = {
        '\t': 'tab',
        ';': 'semicolon',
        ',': 'comma',
    }
    lineterminators = {
        '\r\n': '\\r\\n',
        '\r': '\\r',
        '\n': '\\n',
    }
    sniff_buffer_size = 100000

    def check(self):
        # check using seperate function for inheritance
        result = self.check_csv()
        if result:
            self.rows = list(csv.reader(io.StringIO(self.file.string), self.file.csv_dialect))
            self.lines = self.file.string.splitlines()

        logger.debug('result=%s', result)
        return result

    def check_csv(self):
        try:
            # check if the csv dialect was already found
            self.file.csv_dialect
            return True
        except AttributeError:
            if self.file.string is not None:
                # check different delimiters one by one
                for delimiter in self.delimiters.keys():
                    try:
                        self.file.csv_dialect = csv.Sniffer().sniff(self.file.string[:self.sniff_buffer_size], delimiters=delimiter)
                        return True
                    except csv.Error:
                        pass

        return False

    def get_tables(self):
        tables = []
        table = self.append_table(tables)

        # loop over rows and sort into blocks of similar shape
        blocks = []
        block = {}
        for index, row in enumerate(self.rows):
            shape = self.get_shape(row)
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
                    if prev_block:
                        this_row = self.rows[block['indexes'][0]]
                        prev_row = self.rows[prev_block['indexes'][-1]]

                        if len(prev_row) > 0 and len(prev_row) <= len(this_row):
                            # add the column names as metadata
                            table['metadata'] = {
                                'column_{:02d}'.format(idx): str(value) for idx, value in enumerate(prev_row)
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
                    name = table['metadata'].get('column_{:02d}'.format(idx))
                    table['columns'].append({
                        'key': str(idx),
                        'name': 'Column #{} ({})'.format(idx, name) if name else 'Column #{}'.format(idx)
                    })

            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))

        return tables

    def get_metadata(self):
        metadata = super().get_metadata()
        metadata['lineterminator'] = self.lineterminators.get(self.file.csv_dialect.lineterminator, self.file.csv_dialect.lineterminator)
        metadata['quoting'] = str(self.file.csv_dialect.quoting)
        metadata['doublequote'] = str(self.file.csv_dialect.doublequote)
        metadata['delimiter'] = self.delimiters.get(self.file.csv_dialect.delimiter, self.file.csv_dialect.delimiter)
        metadata['quotechar'] = self.file.csv_dialect.quotechar
        metadata['skipinitialspace'] = str(self.file.csv_dialect.skipinitialspace)
        return metadata

    def get_shape(self, row):
        shape = []
        for cell in row:
            value = cell.strip()
            if value in self.empty_values:
                shape.append('')
            elif self.float_pattern.match(value):
                shape.append('f')
            else:
                shape.append('s')

        return shape

    def compare_shape(self, shape_a, shape_b):
        # this function compares two shapes, shapes are considered equal if
        # floats or strings are at the same positions, spaces are considered wildcards
        # since they could be both floats or strings
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

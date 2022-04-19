import copy
import csv
import io
import logging

from .base import Reader

logger = logging.getLogger(__name__)

TABLE_MIN_ROWS = 20

DELIMITERS = {
    '\t': 'tab',
    ' ': 'space',
    ';': 'semicolon',
    ',': 'comma',
}
LINETERMINATORS = {
    '\r\n': '\\r\\n',
    '\r': '\\r',
    '\n': '\\n',
}


class CSVReader(Reader):
    identifier = 'csv_reader'
    priority = 100

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        result = False
        if self.encoding != 'binary':
            file_string = self.file_content.decode(self.encoding)

            # check different delimiters one by one
            for delimiter in DELIMITERS.keys():
                try:
                    self.dialect = csv.Sniffer().sniff(file_string, delimiters=delimiter)
                    result = True
                    break
                except csv.Error:
                    pass

        if result:
            io_string = io.StringIO(file_string)
            self.lines = list(copy.copy(io_string))
            self.rows = list(csv.reader(io_string, self.dialect))

        logger.debug('result=%s', result)
        return result

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
            if len(block['indexes']) < TABLE_MIN_ROWS or not block['shape']:
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

                table['rows'] += [self.rows[index] for index in block['indexes']]

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

            table['metadata']['rows'] = len(table['rows'])
            table['metadata']['columns'] = len(table['columns'])

        return tables

    def get_metadata(self):
        metadata = super().get_metadata()
        metadata['lineterminator'] = LINETERMINATORS.get(self.dialect.lineterminator, self.dialect.lineterminator)
        metadata['quoting'] = self.dialect.quoting
        metadata['doublequote'] = self.dialect.doublequote
        metadata['delimiter'] = DELIMITERS.get(self.dialect.delimiter, self.dialect.delimiter)
        metadata['quotechar'] = self.dialect.quotechar
        metadata['skipinitialspace'] = self.dialect.skipinitialspace
        return metadata

    def get_shape(self, row):
        shape = []
        for cell in row:
            if cell.strip() == '':
                shape.append('')
            else:
                try:
                    float(cell.replace(',', '.'))
                    shape.append('f')
                except ValueError:
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

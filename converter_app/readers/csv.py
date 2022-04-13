import copy
import csv
import io
import logging

from .base import Reader

logger = logging.getLogger(__name__)


class CSVReader(Reader):
    identifier = 'csv_reader'
    priority = 100

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        if self.encoding == 'binary':
            result = False
        else:
            file_string = self.file_content.decode(self.encoding)

            try:
                self.dialect = csv.Sniffer().sniff(file_string, delimiters=';,\t')
            except csv.Error:
                result = False
            else:
                io_string = io.StringIO(file_string)
                self.lines = copy.copy(io_string)
                self.reader = csv.reader(io_string, self.dialect)
                result = True

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        table = {
            'header': [],
            'metadata': {},
            'columns': [],
            'rows': []
        }
        table_shape = None
        header = False

        # loop through the rows in reverse order from bottom to top
        reverse_lines = reversed(list(self.lines))
        reverse_rows = reversed(list(self.reader))
        for line, row in zip(reverse_lines, reverse_rows):
            shape = self.get_shape(row)
            if table_shape is None:
                # store shape of the first row from the end of the table
                table_shape = shape

            if header:
                table['header'].append(line)
            elif shape != table_shape:
                # this is the last row of the header, check if these are column names
                if list(map(bool, shape)) == list(map(bool, table_shape)):
                    # add the column names as metadata
                    table['metadata'] = {
                        'column_{:02d}'.format(idx): str(value) for idx, value in enumerate(row)
                    }

                else:
                    # add the line as a regular header line
                    table['header'].append(line)

                # set the header switch to true
                header = True
            else:
                table['rows'].append(row)

        table['header'] = list(reversed(table['header']))
        table['rows'] = list(reversed(table['rows']))
        table['columns'] = self.get_columns(table['metadata'].values(), len(table_shape))

        return [table]

    def get_columns(self, column_names, n_columns):
        if column_names:
            return [{
                'key': str(idx),
                'name': 'Column #{} ({})'.format(idx, column_name)
            } for idx, column_name in enumerate(column_names)]
        else:
            # add the row as columns
            return [{
                'key': str(idx),
                'name': 'Column #{}'.format(idx)
            } for idx in range(n_columns)]

    def get_shape(self, row):
        shape = []
        for cell in row:
            if cell.strip() == '':
                shape.append('s')
            else:
                try:
                    float(cell.replace(',', '.'))
                    shape.append('f')
                except ValueError:
                    shape.append('s')
        return shape

    def get_metadata(self):
        metadata = super().get_metadata()
        metadata['lineterminator'] = self.dialect.lineterminator
        metadata['quoting'] = self.dialect.quoting
        metadata['doublequote'] = self.dialect.doublequote
        metadata['delimiter'] = self.dialect.delimiter
        metadata['quotechar'] = self.dialect.quotechar
        metadata['skipinitialspace'] = self.dialect.skipinitialspace
        return metadata

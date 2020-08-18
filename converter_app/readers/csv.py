import csv
import io
import logging
import string

from .base import Reader

logger = logging.getLogger(__name__)


class CSVReader(Reader):
    identifier = 'csv_reader'

    def check(self):
        file_string, self.encoding = self.peek_ascii()

        try:
            self.dialect = csv.Sniffer().sniff(file_string, delimiters=';,\t')
        except csv.Error:
            result = False
        else:
            result = True

        logger.debug('result=%s', result)
        return result

    def get_data(self):
        io_string = io.StringIO(self.file_reader.read().decode(self.encoding))
        reader = csv.reader(io_string, self.dialect)

        columns = []
        rows = []
        for row in reader:
            if not columns:
                columns = [{
                    'key': str(idx),
                    'name': string.ascii_uppercase[idx]
                } for idx, value in enumerate(row)]
            rows.append(row)

        return [{
            'header': [],
            'columns': columns,
            'rows': rows
        }]

import logging

from .base import Reader

logger = logging.getLogger(__name__)


class JascoReader(Reader):
    identifier = 'jasco_reader'
    priority = 99
    header_length = 8

    def check(self):
        result = False
        if self.file.string is not None:
            if len(self.file.string.splitlines()) == 1:
                file_lines = self.file.string.split(',')
                if file_lines[self.header_length - 1] == str(len(file_lines) - self.header_length):
                    result = True
        if result:
            self.lines = file_lines

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []
        table = self.append_table(tables)

        for i, line in enumerate(self.lines):
            if i < self.header_length:
                table['header'].append(line)
            else:
                x, y = line.split()
                table['rows'].append((self.get_value(x), self.get_value(y)))

        # build columns
        for table in tables:
            table['columns'] = []
            if table['rows']:
                for idx in range(len(table['rows'][0])):
                    table['columns'].append({
                        'key': str(idx),
                        'name': 'Column #{}'.format(idx)
                    })

            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))

        return tables

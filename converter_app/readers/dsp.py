import logging

from .base import Reader

logger = logging.getLogger(__name__)


class DSPReader(Reader):
    identifier = 'dsp_reader'
    priority = 95

    def check(self):
        result = False
        if self.file.suffix.lower() == '.dsp' and self.file.mime_type == 'text/plain':
            first_line = self.file.string.splitlines()[0]
            result = 'sinacsa' in first_line

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
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

        if table['rows']:
            table['columns'] = [{
                'key': str(idx),
                'name': 'Column #{}'.format(idx)
            } for idx, value in enumerate(table['rows'][0])]

        table['metadata']['rows'] = str(len(table['rows']))
        table['metadata']['columns'] = str(len(table['columns']))

        return tables

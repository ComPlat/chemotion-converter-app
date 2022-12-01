import logging

from .ascii import AsciiReader

logger = logging.getLogger(__name__)


class SemReader(AsciiReader):
    identifier = 'sem_reader'
    priority = 95

    def check(self):
        result = False
        if super(SemReader, self).check():
            first_line = self.file.string.splitlines()[0]
            result = first_line.startswith('$SEM_DATA_VERSION')

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []
        table = self.append_table(tables)
        table_mode = False
        previous_count = None
        for line in self.file.fp.readlines():
            row: str = line.decode(self.file.encoding).rstrip()
            row_array = row.split(' ')
            if table_mode:
                if previous_count + 1 != len(row_array):
                    table_mode = False
                    table['metadata']['rows'] = len(table['rows'])
                    table['metadata']['columns'] = len(table['columns'])
                    table = self.append_table(tables)
                else:
                    float_match = [self.get_value(float_str) for float_str in row_array]
                    table['rows'].append(float_match)
            if not table_mode:
                if len(row_array) > 1 and all([x.startswith("$") for x in row_array]):
                    table_mode = True
                    previous_count = len(row_array)
                    table['columns'] = [{
                        'key': str(idx),
                        'name': value
                    } for idx, value in enumerate(row_array)]
                else:
                    table['header'].append(row)
                    if len(row_array) > 1:
                        table['metadata'][row_array[0].replace("$", "")] = ", ".join(row_array[1:])
                    else:
                        table['metadata'][row_array[0].replace("$", "")] = "True"

        table['metadata']['rows'] = len(table['rows'])
        table['metadata']['columns'] = len(table['columns'])
        return tables


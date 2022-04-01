import logging
import json

from pathlib import Path

from .base import Reader

logger = logging.getLogger(__name__)


class PsSessionReader(Reader):
    identifier = 'pssession_reader'
    priority = 10

    def check(self):
        logger.debug('file_name=%s content_type=%s mime_type=%s encoding=%s',
                     self.file_name, self.content_type, self.mime_type, self.encoding)

        if Path(self.file_name).suffix != '.pssession':
            result = False
        else:
            result = True

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []

        data = json.load(self.file)
        for measurement in data['measurements']:
            # each measurement is a table
            table = {
                'metadata': {
                    'type': data['type']
                },
                'header': [],
                'columns': [],
                'rows': []
            }

            # add measurement fields to the metadata
            for key in ['title', 'timestamp', 'deviceused', 'deviceserial']:
                table['metadata'][key] = str(measurement[key])

            columns = []
            for idx, values in enumerate(measurement['dataset']['values']):
                # each array is a column
                table['columns'].append({
                    'key': str(idx),
                    'name': 'Column #{} ({})'.format(idx, values['description'])
                })

                # append the "datavalues" to list data list of lists
                columns.append([datavalues['v'] for datavalues in values['datavalues']])

            # transpose data list of lists
            table['rows'] = list(map(list, zip(*columns)))

            tables.append(table)

        return tables

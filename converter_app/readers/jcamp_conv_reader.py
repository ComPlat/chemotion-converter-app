import logging

from numpy import ndarray

from .base import Reader
from jcamp import jcamp_read

logger = logging.getLogger(__name__)


class JcampReader(Reader):
    identifier = 'jcamp_reader'
    priority = 80

    def check(self):
        result = self.file.suffix.lower() in ['.dx', '.jdx', '.jcm']

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []
        table = self.append_table(tables)
        res = jcamp_read(self.file.fp)
        for (k,v) in res.items():
            if isinstance(v, ndarray):
                if len(table['rows']) == 0:
                    table['rows'] = [[x] for x in v.tolist()]
                else:
                    for (i, sv) in enumerate(v):
                        table['rows'][i].append(sv)

                table['columns'].append({
                    'key': str(len(table['columns'])),
                    'name': k
                })
            else:
                table['metadata'][k] = str(v)

        table['metadata']['rows'] = str(len(table['rows']))
        table['metadata']['columns'] = str(len(table['columns']))
        return tables


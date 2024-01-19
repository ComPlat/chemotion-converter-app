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
                pass
            else:
                table['metadata'][k] = str(v)

        table['metadata']['rows'] = str(0)
        table['metadata']['columns'] = str(0)
        return tables


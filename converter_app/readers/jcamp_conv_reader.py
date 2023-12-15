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

    def add_to_meta(self, table, k, src):
        if isinstance(src, list):
            src_iter = enumerate(src)
        elif isinstance(src, dict):
            src_iter = src.items()
        elif isinstance(src, ndarray) or src is None:
            return
        else:
            table['metadata'][k] = str(src)[:255]
            return
        for (k,v) in src_iter:
            self.add_to_meta(table, k, v)

    def get_tables(self):
        tables = []
        table = self.append_table(tables)
        res = jcamp_read(self.file.fp)
        self.add_to_meta(table, None, res)
        table['metadata']['rows'] = str(0)
        table['metadata']['columns'] = str(0)
        return tables


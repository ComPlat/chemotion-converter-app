import logging

from jcamp import jcamp_read
from numpy import ndarray

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class JcampReader(Reader):
    """
    Reads JCAMP files: extentions: .dx, .jdx, .jcm
    """
    identifier = 'jcamp_reader'
    priority = 80

    def check(self):
        """
        :return: True if it fits
        """

        jsamp_extentions = ['.dx', '.jdx', '.jcm']

        if self.is_tar_ball:
            self.file = next((x for x in self.file_content if x.suffix.lower() in jsamp_extentions), None)
            if self.file is None:
                return False

        result = self.file.suffix.lower() in jsamp_extentions

        logger.debug('result=%s', result)
        return result

    def _add_to_meta(self, table, key, src):
        if isinstance(src, list):
            src_iter = enumerate(src)
        elif isinstance(src, dict):
            src_iter = src.items()
        elif isinstance(src, ndarray) or src is None:
            return
        else:
            table['metadata'][key] = str(src)[:255]
            return
        for (k, v) in src_iter:
            self._add_to_meta(table, k, v)

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        res = jcamp_read(self.file.fp)
        self._add_to_meta(table, None, res)
        table['rows'] = [[res['y'][i], val] for i, val in enumerate(res['x'])]

        return tables


Readers.instance().register(JcampReader)

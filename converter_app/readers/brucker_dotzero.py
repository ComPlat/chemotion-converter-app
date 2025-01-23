import logging

from brukeropusreader.opus_parser import parse_meta, parse_data
from numpy import ndarray

from converter_app.readers import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)


class DotZeroReader(Reader):
    """
    Reads .0 files using the package: https://github.com/qedsoftware/brukeropusreader
    """
    identifier = 'dot_zero_reader'
    priority = 79

    def __init__(self, file, *tar_files):
        super().__init__(file, *tar_files)
        self._dotzero_file = []
        self._dx_name = None

    def check(self):
        """
        :return: True if it fits
        """

        dotzero_extentions = ['.0']

        if self.is_tar_ball:
            self._dotzero_file = [x for x in self.file_content if x.suffix.lower() in dotzero_extentions]
            dx_file = next((x for x in self.file_content if x.suffix.lower() == '.dx'), None)
            if dx_file is not None:
                self._dx_name = dx_file.name[:-3]

        if self.file.suffix.lower() in dotzero_extentions:
            self._dotzero_file.append(self.file)

        return len(self._dotzero_file) > 0

    def _add_to_meta(self, table, src, k=None):
        if k is None:
            k = []
        if isinstance(src, list):
            src_iter = enumerate([])
        elif isinstance(src, dict):
            src_iter = src.items()
        elif isinstance(src, ndarray) or src is None:
            return
        else:
            table['metadata']['.'.join(k)] = str(src)[:255]
            return
        for (key, v) in src_iter:
            self._add_to_meta(table, v, k + [key])

    def prepare_tables(self):
        tables = []

        for dotzero_file in self._dotzero_file:
            data = dotzero_file.content
            meta_data = parse_meta(data)
            opus_data = parse_data(data, meta_data)
            if dotzero_file.name == self._dx_name:
                table = self.append_table([])
                tables.insert(0, table)
            else:
                table = self.append_table(tables)
            table['metadata']['__FILE_NAME__'] = dotzero_file.name
            self._add_to_meta(table, opus_data)
            ab_x = opus_data.get_range("AB")
            table['rows'] = [[val,  opus_data["AB"][i], opus_data["ScSm"][i], opus_data["ScRf"][i]] for i, val in enumerate(ab_x)]

            table['columns'] += [{
                'key': f'{idx}',
                'name': value
            } for idx, value in enumerate(["X", "AB", "ScSm", "ScRf"])]
        return tables


Readers.instance().register(DotZeroReader)

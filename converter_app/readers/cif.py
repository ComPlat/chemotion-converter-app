import logging
import os
import re
import tempfile
from zipfile import ZipFile

from gemmi import cif
from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class CifReader(Reader):
    """
    Reader for .cif files. Files can be Zipped
    """
    identifier = 'cif_reader'
    priority = 10
    file_prefix = '.cif'
    cif = None

    junk_size_threshold = 500

    # two or more chars in row
    header_pattern = re.compile(r'^_[A-Za-z]{2,}')
    col_header_pattern = re.compile(r'^\s+_')
    data_row_pattern = re.compile(r'^\s+[^\s_]')
    data_str_pattern = r"'[^'\\]*(?:\\.[^'\\]*)*'"
    data_number_pattern = r"-?\d+\.?\d*\(?\d*\)?"
    data_symbol_pattern = r"[A-Za-z]{1,3}\d*"
    data_pattern = re.compile(rf"{data_str_pattern}|{data_symbol_pattern}|{data_number_pattern}")

    def _commonprefix(self, a):
        prefix_len = len(a[0])
        for x in a[1:]:
            prefix_len = min(prefix_len, len(x))
            while not x.startswith(a[0][: prefix_len]):
                prefix_len -= 1

        return a[0][: prefix_len]

    def check(self):
        """
        :return: True if it fits
        """
        if self.file.suffix.lower() == '.zip' and self.file.mime_type == 'application/zip':
            with ZipFile(self.file.fp, 'r') as zip_obj:
                try:
                    file_name = next(x for x in zip_obj.namelist() if x.lower().endswith(self.file_prefix))
                    with os.path.join(tempfile.TemporaryDirectory().name, self.file.name) as zipdir:
                        os.makedirs(zipdir)
                        path_file_name = zip_obj.extract(file_name, zipdir)
                        with open(path_file_name, 'rb') as f:
                            fs = FileStorage(stream=f, filename=os.path.basename(file_name),
                                             content_type='chemical/x-cif')
                            self.file = File(fs)
                except:
                    logger.debug('result=%s', False)
                    return False

        result = self.file.suffix.lower() == self.file_prefix and self.file.mime_type == 'text/plain'
        if result:
            try:
                self.cif = cif.read_string(self.file.content)  # copy all the data from mmCIF file
            except ValueError as e:
                if str(e).endswith('expected block header (data_)'):
                    content = 'data_' + re.split('^data_', self.file.string, flags=re.M)[-1]
                    try:
                        self.cif = cif.read_string(content)  # copy all the data from mmCIF file
                    except ValueError:
                        result = False

        return result

    def prepare_tables(self):
        if self.cif is None:
            return []
        all_tables = []
        for block in self.cif:  # mmCIF has exactly one block
            tables = []
            all_tables.append(tables)
            meta_table = self.append_table(tables)
            junk_table_header = []
            has_junk = False

            meta_table['header'].append(f"Block_name = {block.name}")
            meta_table['metadata']["Block_name"] = block.name

            for item in block:
                if item.pair is not None:
                    if 'highest difference peak' in ''.join(item.pair).lower():
                        meta_table['header'].append(' = '.join(item.pair[:2]))
                    elif len(item.pair[1]) > self.junk_size_threshold:
                        has_junk = True
                        junk_table_header.append(' = '.join(item.pair[:2]))
                    else:
                        meta_table['header'].append(' = '.join(item.pair[:2]))
                        meta_table['metadata'][item.pair[0]] = re.sub(r"^[;\s']+|[;\s']+$", "", item.pair[1])
                elif item.loop is not None:
                    table = self.append_table(tables)
                    table.add_metadata("Block_name", block.name)
                    prefix = self._commonprefix(item.loop.tags)
                    meta_table['metadata']['Loop_name'] = prefix
                    for tag in item.loop.tags:
                        table['header'].append(tag)
                        table['columns'].append({
                            'key': str(len(table['columns']) + 1),
                            'name': tag
                        })

                    for i in range(0, len(item.loop.values), len(item.loop.tags)):
                        table['rows'].append(
                            item.loop.values[i:(i + len(item.loop.tags))])

            if has_junk:
                junk_table = self.append_table(tables)
                junk_table.add_metadata("Block_name", block.name)
                junk_table['header'] = junk_table_header

        all_tables.sort(key=lambda x: len(x), reverse=True)

        return [
            table
            for tables in all_tables
            for table in tables
        ]


Readers.instance().register(CifReader)

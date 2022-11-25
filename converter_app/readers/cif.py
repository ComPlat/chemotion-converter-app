import logging
import re

from gemmi import cif
from .base import Reader

logger = logging.getLogger(__name__)


class CifReader(Reader):
    identifier = 'cif_reader'
    priority = 95
    cif = None

    junk_size_threshold = 500

    # two or more chars in row
    header_pattern = re.compile(r'^_[A-Za-z]{2,}')
    col_header_pattern = re.compile(r'^\s+_')
    data_row_pattern = re.compile(r'^\s+[^\s_]')
    data_str_pattern = r"'[^'\\]*(?:\\.[^'\\]*)*'"
    data_number_pattern = r"-?\d+\.?\d*\(?\d*\)?"
    data_symbol_pattern = r"[A-Za-z]{1,3}\d*"
    data_pattern = re.compile(r"%s|%s|%s" % (data_str_pattern, data_symbol_pattern, data_number_pattern))

    def _commonprefix(self, a):
        prefix_len = len(a[0])
        for x in a[1 : ]:
            prefix_len = min(prefix_len, len(x))
            while not x.startswith(a[0][ : prefix_len]):
                prefix_len -= 1

        return a[0][ : prefix_len]

    def check(self):
        result = self.file.suffix.lower() == '.cif' and self.file.mime_type == 'text/plain'
        if result:
            try:
                self.cif = cif.read_string(self.file.content)  # copy all the data from mmCIF file
            except:
                result = False

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        if self.cif is None:
            return []
        block = self.cif.sole_block()  # mmCIF has exactly one block

        tables = []
        meta_table = self.append_table(tables)
        junk_table_header = []
        has_junk = False

        meta_table['header'].append("Block_name = %s" % block.name)
        meta_table['metadata']["Block_name"] = block.name

        for item in block:
            if item.pair is not None:
                if len(item.pair[1]) > self.junk_size_threshold:
                    has_junk = True
                    junk_table_header.append("%s = %s" % item.pair)
                else:
                    meta_table['header'].append("%s = %s" % item.pair)
                    meta_table['metadata'][item.pair[0]] = re.sub(r"^[;\s']+|[;\s']+$", "", item.pair[1] )
            elif item.loop is not None:
                table = self.append_table(tables)
                prefix = self._commonprefix(item.loop.tags)
                meta_table['metadata']['Loop_name'] = prefix
                for tag in item.loop.tags:
                    table['header'].append(tag)
                    table['columns'].append({
                        'key': str(len(table['columns']) + 1) ,
                        'name': tag
                    })

                for i in range(0, len(item.loop.values), len(item.loop.tags)):
                    table['rows'].append(['R%d' % (i // len(item.loop.tags))] + item.loop.values[i:(i+len(item.loop.tags))])


                table['metadata']['rows'] = len(table['rows'])
                table['metadata']['columns'] = len(table['columns'])

            elif item.frame is not None:
                pass #print('frame', item.frame)

        if has_junk:
            junk_table = self.append_table(tables)
            junk_table['header'] = junk_table_header

        return tables

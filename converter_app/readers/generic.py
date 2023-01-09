import logging
import os
import re
import json

from .base import Reader as Readerbase

from ..models import Reader as Reader

logger = logging.getLogger(__name__)


class GenericReader(Readerbase):
    identifier = 'generic_reader'
    priority = 90

    mode = None

    class ContentManager():

        def __init__(self, table, content, generic_reader):
            self.content = content
            self.table = table
            self.generic_reader = generic_reader
        def read(self, table, row):
            raise NotImplementedError

        def split(self, row):
            sep = self.content.get('seperator', self.table.get('seperator'))
            if sep.get('match') == 'exact':
                return row.split(sep.get('value'))
            if (sep.get('match') == 'regex'):
                rv = re.compile(sep.get('value'))
                return rv.split(row)
            else:
                rv = re.compile('[ \t]')
                return rv.split(row)

        def pre_check(self, row):
            return self.content['include_end'] or not self.generic_reader._check_identifyer(row, self.content.get('end'))
        def post_check(self, row):
            return not self.content['include_end'] or not self.generic_reader._check_identifyer(row, self.content.get('end'))

    class MetaData(ContentManager):

        def read(self, table, row):
            table['header'].append(row)
            row_vals = self.split(row)
            main_key = row_vals.pop(0)
            idx = 0

            for v in row_vals:
                key = main_key
                if key in table['metadata']:
                    key = key + str(idx)
                table['metadata'][key] = v

            return self.post_check(row)

    class MetaDataTable(ContentManager):
        def __init__(self, table, content, generic_reader):
            super().__init__(table, content, generic_reader)
            self.header = None
            self.index = 0

        def read(self, table, row):
            table['header'].append(row)
            row_vals = self.split(row)
            if self.header is None:
                self.header = row_vals
                if self.content.get('col_idx_name') != '' and self.content.get('col_idx_name') in row_vals:
                    self.index = row_vals.index(self.content.get('col_idx_name'))
                return True
            if self.index < len(row_vals):
                main_key = row_vals[self.index]

                for i, v in enumerate(row_vals):
                    key = "ROW_{}_{}".format(main_key, self.header[i])
                    idx = 1
                    while key in table['metadata']:
                        key = "ROW_{}({})_{}".format(main_key, idx, self.header[i])
                        idx += 1
                    table['metadata'][key] = v

            return self.post_check(row)

    class DataTable(ContentManager):
        def __init__(self, table, content, generic_reader):
            super().__init__(table, content, generic_reader)
            self.header = None

        def read(self, table, row):
            row_vals = self.split(row)
            if self.header is None:
                if self.content.get('with_col_header'):
                    self.header = row_vals
                    table['columns'] = [{
                        'key': str(idx),
                        'name': value
                    } for idx, value in enumerate(row_vals)]
                    return True
                else:
                    self.header = row_vals
                    table['columns'] = [{
                        'key': str(idx),
                        'name': "col #%d" % idx
                    } for idx, value in enumerate(row_vals)]


            table['rows'].append(row_vals)
            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))

            return self.post_check(row)

    table_modes = []

    def _check_identifyer(self, s, i):
        if (i.get('match') == 'exact'):
            return i.get('value') == s
        if (i.get('match') == 'regex'):
            rv = re.compile(i.get('value'))
            return rv.search(s)
        return False

    def check(self):
        if self.file.string is not None:
            file_lines = self.file.fp.readlines()

            for reader in Reader.list(self.client_id):
                parser_dict = reader.as_dict
                file_ext = re.split('[,\s]+',
                                    parser_dict.get('identifiers', {}).get('meta', {}).get('file_extension', ''))
                if file_ext == [''] or self.file.suffix in file_ext:
                    result = True
                    for line_check in parser_dict.get('identifiers', {}).get('content', []):
                        line = file_lines[line_check['lineNumber'] - 1]
                        row = line.decode(self.file.encoding).rstrip()
                        if not self._check_identifyer(row, line_check):
                            result = False
                            break

                    if result:
                        self.parser_dict = parser_dict
                        self.lines = file_lines
                        self.identifier = parser_dict['title']
                        logger.debug('result=%s', result)
                        return result

        logger.debug('result=%s', False)
        return False

    def _check_new_mode(self, row):
        for mode in self.parser_dict['tables']:
            if self._check_identifyer(row, mode.get('start')):
                self.mode = {'idx': 0, 'content': [], 'include_start': mode['include_start']}

                for content in mode['content']:
                    if content['type'] == 'DataTable':
                        self.mode['content'].append(
                            self.__class__.DataTable(table=mode, content=content, generic_reader=self))
                    elif content['type'] == 'MetaDataTable':
                        self.mode['content'].append(
                            self.__class__.MetaDataTable(table=mode, content=content, generic_reader=self))
                    elif content['type'] == 'MetaData':
                        self.mode['content'].append(
                            self.__class__.MetaData(table=mode, content=content, generic_reader=self))
                self.mode['idx'] = 0
                return True
        return False

    def get_tables(self):
        tables = []
        table = None


        for line in self.lines:
            row = line.decode(self.file.encoding).rstrip()
            only_new_table = False
            if self._check_new_mode(row):
                table = self.append_table(tables)
                table['metadata']['  TABLE NAME'] = row
                only_new_table = not self.mode['include_start']
                if only_new_table:
                    table['header'].append(row)


            if not only_new_table and self.mode is not None and self.mode['idx'] < len(self.mode['content']):
                if not self.mode['content'][self.mode['idx']].pre_check(row):
                    self.mode['idx'] = self.mode['idx'] + 1

                if self.mode['idx'] < len(self.mode['content']) and not self.mode['content'][self.mode['idx']].read(table, row):
                    self.mode['idx'] = self.mode['idx'] + 1

        return tables

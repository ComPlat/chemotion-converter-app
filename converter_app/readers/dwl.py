import re
import logging

from .base import Reader

logger = logging.getLogger(__name__)


class DWLReader(Reader):
    identifier = 'dwl-reader'
    priority = 10

    #
    class ReaderSate():
        current_tags = []

    def __init__(self, file):
        super().__init__(file)
        self.state = DWLReader.ReaderSate()
        self.table_rows = {'__rows': 0, 'X in (Die(X/Y))': [], 'Y in (Die(X/Y))': []}

    def check(self):
        # check using seperate function for inheritance
        result = self.file.suffix.lower() == '.result' and self.file.mime_type == 'text/plain'
        if result:
            self.lines = self.file.string.splitlines()
            try:
                result = (re.match('^<[^>]+>$', self.lines[0]) is not None) or self.lines[1].startswith('Start') or \
                         self.lines[2].startswith('Status')
            except:
                result = False

        logger.debug('result=%s', result)
        if result: self._check_next_tag(self.lines[0])
        return result

    def _check_next_tag(self, row):
        match: re.Match = re.match('^\s*<(.+)>\s*$', row)
        if match is not None:
            tag_name = match.groups()[0]
            if tag_name.startswith('/'):
                if tag_name[1:] == self.state.current_tags[-1]:
                    self.state.current_tags.pop(-1)
                    return -1
                else:
                    raise ValueError("Tag '{}' does not close!".format(self.state.current_tags[-1]))
            else:
                self.state.current_tags.append(tag_name)
                return 1
        return 0

    def _parse_table_row(self, die_pos, tb_data):
        table_keys = ['Size', 'Offset', 'NOver', 'NumberOfStripes', 'FilledStripes', 'Bidirectional', 'ScanWidth',
                      'SpeedScale', 'FocalLength']
        self.table_rows['X in (Die(X/Y))'].append(die_pos[0])
        self.table_rows['Y in (Die(X/Y))'].append(die_pos[1])
        re_div = re.compile('\(([\.\-\d]+)/([\.\-\d]+)\)\[([^]]+)]')
        re_unit_number = re.compile('([\.\-\d]+)\[([^]]+)]')
        re_boolean = re.compile('True|False')
        for tk in table_keys:
            value = tb_data.get(tk, '').strip()
            m_div = re_div.match(value)
            m_unit = re_unit_number.match(value)
            m_bool = re_boolean.match(value)
            if m_div is not None:
                tk += '[{}]'.format(m_div.groups()[2])
                value = float(m_div.groups()[0]) / float(m_div.groups()[1])
            elif m_unit is not None:
                tk += '[{}]'.format(m_unit.groups()[1])
                value = float(m_unit.groups()[0])
            elif m_bool is not None:
                value = 1 if value == 'True' else 1
            else:
                value = float(value)
            self.table_rows[tk] = self.table_rows.get(tk, ['-'] * self.table_rows['__rows'])
            self.table_rows[tk].append(value)
        self.table_rows['__rows'] += 1
        for (key, val) in self.table_rows.items():
            if key != '__rows' and len(val) < self.table_rows['__rows']:
                val.append('-')

    def get_tables(self):
        tables = []
        table = self.append_table(tables)
        is_die = False
        die_depth = 0
        die_pos = None
        die_table_idx = 0
        die_re = re.compile('Die\((\d+)/(\d+)')
        table_keys = ['Size', 'Offset' 'NOver', 'NumberOfStripes: 5', 'FilledStripes', 'Bidirectional', 'ScanWidth',
                      'SpeedScale: 1', 'FocalLength']

        for idx, line in enumerate(self.lines[1:]):
            line = line.strip()
            nt_res = self._check_next_tag(line)
            if nt_res == 1:
                if table['header'][-1].endswith(':'):
                    table['header'][-1] += " input table # {}".format(len(tables))
                table = self.append_table(tables)
                prev_line = 'Table Name'
                kv = (prev_line.strip(), " -> ".join(self.state.current_tags))
                table['header'].append("{}: {}".format(*kv))
                table['metadata'][kv[0]] = kv[1]
                m = die_re.match(self.state.current_tags[-1])
                if m:
                    if is_die: self._parse_table_row(die_pos, tables[die_table_idx]['metadata'])
                    die_table_idx = len(tables)
                    die_pos = [int(x) for x in m.groups()]
                    die_depth = len(self.state.current_tags)
                    is_die = True
                elif die_depth > len(self.state.current_tags):
                    if is_die: self._parse_table_row(die_pos, tables[die_table_idx]['metadata'])
                    is_die = False
            elif nt_res == 0 and line != '':
                sep = ';' if not line.startswith('Start') else ' --> '
                for elment in line.split(sep):
                    elment = elment.strip()
                    sep = ' ' if line.startswith('Start') or line.startswith('Logfile') else ':'
                    kv = elment.split(sep)
                    table['header'].append(elment)
                    if line.startswith('Logfile'):
                        table['metadata']['Logfile'] = ' '.join(kv[1:])
                    elif len(kv) > 1:
                        table['metadata'][' '.join(kv[:-1])] = kv[-1]

        # loop over tables and append columns
        table = tables[0]
        table['rows'] = [[] for i in range(self.table_rows['__rows'])]
        table['columns'] = []
        idx = 0
        for (columns_key, column) in self.table_rows.items():
            if columns_key == '__rows': continue
            for r_idx, elem in enumerate(column):
                table['rows'][r_idx].append(elem)
            table['columns'].append({
                'key': str(idx),
                'name': columns_key
            })
            idx += 1

        table['metadata']['rows'] = str(len(table['rows']))
        table['metadata']['columns'] = str(len(table['columns']))

        return tables

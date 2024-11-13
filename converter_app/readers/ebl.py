import logging
import re
from enum import Enum
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class EblReader(Reader):
    """
    reads EBL files with extension: .log
    """
    identifier = 'ebl_reader'
    priority = 50

    class _State(Enum):
        META = 0
        POS_TABLE_A = 1
        POS_TABLE_B = 2
        POS_TABLE_C = 3
        POS_TABLE_D = 4
        END = 5

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self.lines = None
        self.pre_header = None
        self.pre_script = None
        self.suffix = []
        self.state = self._State.META

    class _PreProcessor:
        header_lines = 10000

        class _State(Enum):
            HEADER = 0
            SCRIPT = 1
            SCRIPT_END = 2
            META = 3

        state = _State.HEADER

        @classmethod
        def process_header(cls, lines):
            cls.state = cls._State.HEADER
            pre_header = []
            pre_script = []
            for line in lines:
                if cls.state == cls._State.HEADER:
                    if line.startswith('#! /bin/bash'):
                        cls.state = cls._State.SCRIPT
                    else:
                        pre_header.append(line)
                if cls.state == cls._State.SCRIPT_END:
                    if line.startswith('###########################################'):
                        cls.state = cls._State.META
                    else:
                        cls.state = cls._State.SCRIPT
                if cls.state == cls._State.SCRIPT:
                    if line.startswith('###########################################'):
                        cls.state = cls._State.SCRIPT_END
                    pre_script.append(line)
                if cls.state == cls._State.META and line.startswith('Set up default machine parameters'):
                    return pre_header, pre_script, True
            return pre_header, pre_script, False

    def check(self):
        """
        :return: True if it fits
        """
        result = self.file.suffix.lower() == '.log' and self.file.mime_type == 'text/plain'
        if result:
            self.lines = self.file.string.splitlines()
            (self.pre_header, self.pre_script, result) = self._PreProcessor.process_header(
                self.lines[:self._PreProcessor.header_lines])

        return result

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        table['header'] = self.pre_header
        log_path = self.pre_header[0].split(': ')[-1]
        log_path = log_path.split('/')[-1].rstrip('.log').split('_')
        table['metadata']['log-Nummer'] = log_path[0]
        table['metadata']['Layout'] = '_'.join(log_path[1:-2])
        table['metadata']['KNMFi-Projekt'] = log_path[-2]
        table['metadata']['Laufende Nummer'] = log_path[-1]
        for line in self.pre_header:
            if line.startswith('installing beams'):
                table['metadata']['Beams'] = line.split(' ')[-1]
            elif line.startswith('pg select holder'):
                table['metadata']['Holder'] = line.split(' ')[-1]

        table = self.append_table(tables)
        table['header'] = self.pre_script
        for line in self.pre_script:
            line = line.strip()
            if line.startswith('export cjob_beam'):
                table['metadata']['cjob_beam'] = line.split('=')[-1].strip('"')
            elif line.startswith('export cjob_pattern'):
                table['metadata']['cjob_pattern'] = line.split('=')[-1].strip('"')
        table = self.append_table(tables)
        pos_table = self.append_table(tables)
        for line in self.lines[len(self.pre_script) + len(self.pre_header):]:

            text = re.split(r'\s*:\s+', line)
            if self.state != self._State.META:

                values = [x for x in re.split(r'[|\s]+', text[0].strip()) if re.match(r'-?[\d]*\.?[\d]+', x)]
                if len(values) > 2 and len(values) < 5:
                    if self.state == self._State.POS_TABLE_A:
                        pos_table['metadata']['A [1,2]'] = values[0]
                        pos_table['metadata']['A [1,3]'] = values[1]
                        pos_table['metadata']['A [1,4]'] = values[2]
                    else:
                        row = self.state.value - self._State.POS_TABLE_B.value
                        y_label = ['2', '3', '4'][row]
                        self._add_value(pos_table, f"A [{y_label},1]", values[0])
                        self._add_value(pos_table, f"A [{y_label},2]", values[1])
                        self._add_value(pos_table, f"A [{y_label},3]", values[2])
                        self._add_value(pos_table, f"A [{y_label},4]", values[3])
                    self.state = self._State((self.state.value + 1) % self._State.END.value)
                pos_table['header'].append(line)
                continue
            if len(text) > 1 and len(text) % 2 == 1:
                for idx in range(1, len(text), 2):
                    m = re.match(r'^(.+?(?=\s{3}))\s{3,}(.+)$', text[idx])
                    text.pop(idx)
                    if m is not None:
                        g = list(m.groups())
                        g.reverse()
                        for x in g:
                            text.insert(idx, x)

            if len(text) == 0 or len(text) == 1 and text[0] == '':
                continue
            if len(text) == 1 and text[0].strip().startswith('measured heights in'):
                pos_table['header'].append(text[0].strip())
                pos_table['metadata']['UNIT'] = re.sub(r'(measured heights in)|(on the substrate)|\s', '', text[0])
                self.state = self._State.POS_TABLE_A
            if len(text) == 1 and text[0].endswith(':'):
                if not text[0].startswith(' '):
                    self.suffix = [text[0][:-1]]
                else:
                    if len(self.suffix) < 2:
                        self.suffix.append('')
                    self.suffix[1] = text[0][:-1]
            elif len(text) % 2 == 0 and text:
                if not text[0].startswith(' '):
                    self.suffix = []
                    suffix = ''
                else:
                    suffix = '.'.join(self.suffix) + '.'
                text = [re.sub(r'\s{2,}', ' ', x.strip()) for x in text]
                for idx in range(0, len(text), 2):
                    (k, values) = (f"{suffix}{text[idx]}", text[idx + 1])
                    for value in re.split(r'\s*,\s*', values):
                        self._add_key_value(table, k, value)

            table['header'].append(line)

        return tables

    def _add_value(self, table, k, v):
        mv = re.match(r'(-?[\d]+.?[\d]*)[\s_]{1,}(\w+)', v)
        if mv is not None:
            table['metadata'][k + '[UNIT]'] = mv.groups()[1]
            table['metadata'][k] = mv.groups()[0]
        else:
            table['metadata'][k] = v

    def _add_key_value(self, table, k, v):
        if k not in table['metadata']:
            self._add_value(table, k, v)
            return
        idx = 0
        while True:
            idx += 1
            nk = f'{k}({idx})'
            if nk not in table['metadata']:
                self._add_value(table, nk, v)
                return


Readers.instance().register(EblReader)

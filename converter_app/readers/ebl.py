import logging
import re
from enum import Enum

from gemmi import cif
from .base import Reader

logger = logging.getLogger(__name__)


class EblReader(Reader):
    identifier = 'ebl_reader'
    priority = 50


    class PreProcessor:
        header_lines = 400
        class State(Enum):
            HEADER = 0
            SCRIPT = 1
            SCRIPT_END = 2
            META = 3

        state = State.HEADER
        @classmethod
        def process_header(cls, lines):
            pre_header = []
            pre_script = []
            for line in lines:
                if cls.state == cls.State.HEADER:
                    if line.startswith('#! /bin/bash'):
                        cls.state = cls.State.SCRIPT
                    else:
                        pre_header.append(line)
                if cls.state == cls.State.SCRIPT_END:
                    if line.startswith('###########################################'):
                        cls.state = cls.State.META
                    else:
                        cls.state = cls.State.SCRIPT
                if cls.state == cls.State.SCRIPT:
                    if line.startswith('###########################################'):
                        cls.state = cls.State.SCRIPT_END
                    pre_script.append(line)
                if cls.state == cls.State.META and  line.startswith('Set up default machine parameters'):
                    return pre_header, pre_script, True
            return pre_header, pre_script, False


    def check(self):
        result = self.file.suffix.lower() == '.log' and self.file.mime_type == 'text/plain'
        if result:
            self.lines = self.file.string.splitlines()
            (self.pre_header, self.pre_script, result) = self.__class__.PreProcessor.process_header(self.lines[:self.__class__.PreProcessor.header_lines])

        logger.debug('result=%s', result)
        return result

    def get_tables(self):
        tables = []
        table = self.append_table(tables)
        table['header'] = self.pre_header
        table = self.append_table(tables)
        table['header'] = self.pre_script
        table = self.append_table(tables)
        for line in self.lines[len(self.pre_script) + len(self.pre_header):]:
            text = []
            for x in re.split('\s*:\s+', line):
                text += re.split('\s{3,}',x)
            table['header'].append(str(text))

        for table in tables:
            if table['rows']:
                table['columns'] = [{
                    'key': str(idx),
                    'name': 'Column #{}'.format(idx)
                } for idx, value in enumerate(table['rows'][0])]

            table['metadata']['rows'] = str(len(table['rows']))
            table['metadata']['columns'] = str(len(table['columns']))


        return tables

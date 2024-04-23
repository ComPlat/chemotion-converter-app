import logging
from itertools import chain
from converter_app.readers.helper.reader import Readers
from .pdf import PdfReader

logger = logging.getLogger(__name__)


class EaPdfReader(PdfReader):
    """
    Subclass of PDF reader
    """
    identifier = 'pdf_ea_reader'
    priority = 99
    meta_join_char = '\n'

    def check(self):
        """
        :return: True if it fits
        """
        res = super().check()
        if res:
            res = len(self.text_data) == 1 and '_' in self.text_data and self.text_data['_'][-1][
                'text'].strip().startswith('Signature')
        return res

    def prepare_line(self, line):
        """
        overwrides the PDFreader prepare_line
        :param line: String PDF line
        :return:
        """
        split_line = line.split('\n')
        text_obj = {'text': line.replace('\n', ' ').strip(), 'meta': {}}
        if len(split_line) >= 2:
            text_obj['meta'][split_line[0]] = '\n'.join(split_line[1:])

        return text_obj

    def prepare_tables(self):
        tables = []
        text_data = self.text_data['_']
        table = self.append_table(tables)
        table['metadata'].add_unique('User name', text_data[0]['text'])
        a = [[x] + y.split('\n') for x, y in text_data[1]['meta'].items()]
        for elem in list(chain.from_iterable(a)):
            kv = elem.split(':')
            table['metadata'].add_unique(kv[0], ':'.join(kv[1:]))
        keys = list(text_data[2]['meta'].values())[0].split('\n')[:-2]
        table['header'].append(text_data[2]['text'])
        for line in text_data[3:]:
            table['header'].append(line['text'])
            for k, v in line['meta'].items():
                values = v.split('\n')
                for idx, elem_k in enumerate(keys):
                    if len(values) > idx:
                        table['metadata'].add_unique(f"{k}_{elem_k}", values[idx])

        return tables


Readers.instance().register(EaPdfReader)

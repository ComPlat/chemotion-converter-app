import logging
from converter_app.readers.pdf import PdfReader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class PdfLithozReader(PdfReader):
    """
    Reads metadata from a lithoz PDF
    """
    identifier = 'pdf_lithoz_reader'
    priority = 99

    def check(self):
        """
        :return: True if it fits
        """
        res = super().check()
        if res:
            res = len(self.text_data) == 6 and 'Zusammenfassung' in self.text_data
        return res

    def _handle_kartuschen(self, pdf_data, table):
        headers = [pdf_data[1]['line_split'][0], ' '.join(pdf_data[1]['line_split'][1:])]
        headers += [pdf_data[2]['line_split'][0], ' '.join(pdf_data[2]['line_split'][1:])]
        for row in pdf_data[3:]:
            while len(row['line_split']) < 4:
                row['line_split'].insert(1, '-')
            for idx, header in enumerate(headers):
                table['metadata'].add_unique(header, row['line_split'][idx])

    def prepare_tables(self):
        tables = []
        text_data = self.text_data
        for table_name, pdf_data in text_data.items():
            table = self.append_table(tables)

            table['metadata']['___SECTION'] = table_name

            if table_name == 'Kartuschen':
                self._handle_kartuschen(pdf_data, table)
                continue
            elif table_name == 'Zusammenfassung':
                comment_idx_s = next((i for i,v in enumerate(pdf_data) if 'Run anpassen' in v['meta']), len(pdf_data))
                comment_idx_e = next((i for i,v in enumerate(pdf_data[comment_idx_s + 1:]) if 'Zusammenfassung' == v['text']), 0) + comment_idx_s
                if comment_idx_s >= comment_idx_e:
                    table['metadata']['__comment'] = '-'
                else:
                    table['metadata']['__comment'] = ' '.join([t['text'] for t in pdf_data[comment_idx_s + 1:comment_idx_e + 1]])

            for line in pdf_data:
                if 'Schichtbereich von' in line['text']:
                    table = self.append_table(tables)
                    line['meta']['Schichtbereich'] = line['text'][len('Schichtbereich'):].strip()
                table['header'].append(line['text'])
                for k, v in line['meta'].items():
                    table['metadata'].add_unique(k, v)

        return tables


Readers.instance().register(PdfLithozReader)

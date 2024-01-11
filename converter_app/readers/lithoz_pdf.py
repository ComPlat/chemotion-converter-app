import logging
from .pdf import PdfReader

logger = logging.getLogger(__name__)


class PdfLithozReader(PdfReader):
    identifier = 'pdf_lithoz_reader'
    priority = 99

    def check(self):
        res = super().check()
        if res:
            res = len(self.text_data) == 6 and 'Zusammenfassung' in self.text_data
        return res


    def get_tables(self):
        tables = []
        text_data = self.text_data
        for table_name, pdf_data in text_data.items():
            table = self.append_table(tables)

            table['metadata']['___SECTION'] = table_name
            for line in pdf_data:
                if 'Schichtbereich von' in line['text']:
                    table = self.append_table(tables)
                    line['meta']['Schichtbereich'] = line['text'][len('Schichtbereich'):].strip()
                table['header'].append(line['text'])
                for k, v in line['meta'].items():
                    table['metadata'].add_unique(k, v)

        return tables

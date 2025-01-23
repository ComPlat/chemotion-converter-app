import logging
from html.parser import HTMLParser

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)



class _MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._current_path = []
        self._tables = []
        self._current_row = []

    def handle_starttag(self, tag, attrs):
        self._current_path.append(tag)
        if tag == 'table':
            self._tables.append({'rows':[], 'cols':[]})
        elif tag == 'tr':
            self._current_row = []
        elif tag in ['th', 'td']:
            self._current_row.append({'tag': tag, 'data': ''})

    def handle_endtag(self, tag):
        while tag != self._current_path.pop(-1):
            pass
        if tag == 'tr':
            if self._current_path[-1] == 'thead' or all(x['tag'] == 'th' for x in self._current_row):
                self._tables[-1]['cols'] = [x['data'] for x in self._current_row]
            else:
                self._tables[-1]['rows'].append([x['data'] for x in self._current_row])

    def handle_data(self, data):
        if len(self._current_path) > 0 and self._current_path[-1] in ['th', 'td']:
            self._current_row[-1]['data'] = data

    def get_tables(self):
        return self._tables

class HtmlReader(Reader):
    """
        Implementation of the HTML Reader. It extends converter_app.readers.helper.base.Reader
    """
    identifier = 'html_reader'
    priority = 100

    def check(self):
        return self.file.suffix.lower() == '.html'

    def prepare_tables(self):
        tables = []
        parser = _MyHTMLParser()
        parser.feed(self.file.string)
        temp_tables = parser.get_tables()
        for tt in temp_tables:
            table = self.append_table(tables)
            for row in tt['rows']:
                shape = self.get_shape(row)
                if 's' in shape:
                    for val in row[1:]:
                        table['metadata'].add_unique(row[0], val)

        return tables


Readers.instance().register(HtmlReader)

import logging

from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.unit_converter import convert_units, search_terms_matrix
from converter_app.readers.html import HtmlReader

logger = logging.getLogger(__name__)


class CsmReader(HtmlReader):
    """
        Implementation of the Csm Reader. It extends converter_app.readers.helper.base.Reader
    """
    identifier = 'csm_reader'
    priority = 10

    def check(self):
        is_check = super().check()
        if is_check:
            return '<div id="metainfo">' in self.file.string

    def prepare_tables(self):
        tables = super().prepare_tables()
        table = self.append_table(tables)
        for term in search_terms_matrix:
            for key, val in tables[-2]['metadata'].items():
                if key == term[1]:
                    table['metadata'].add_unique(term[0], val)
        table = self.append_table(tables)
        table['metadata'] = convert_units(tables[-1]['metadata'] | tables[-2]['metadata'], 1)
        return tables


Readers.instance().register(CsmReader)

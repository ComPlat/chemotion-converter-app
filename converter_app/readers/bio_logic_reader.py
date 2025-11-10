import logging

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers
from converter_app.readers.mpl import MplReader
from converter_app.readers.mpr import MprReader

logger = logging.getLogger(__name__)


class BioLogic(Reader):
    """
    BioLogic files are a composed archive of 4 Files a .mps, .mpl .mpr and .mgr

    - .mgr -> A cml graph description (not needed for convertion)
    - .mps -> Summery of a set of procedures  (not needed for convertion)
    - .mpl -> Log file, contain metadata
    - .mpr -> Binary file, contain data and metadata
    """

    identifier = 'bio_logic_080ecac4-8fa2-4c47-b7cc-4ef5db082b07'
    uuid = '080ecac4-8fa2-4c47-b7cc-4ef5db082b07'
    priority = 20

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self.mpl_reader = None
        self.mpr_reader = None

    def check(self):
        mpr_found = False
        if self.file.is_tar_archive:
            for file in self.file_content:
                self.mpr_reader = MprReader(file)
                if self.mpr_reader.check():
                    mpr_found = True
                    break
            if not mpr_found:
                return False
            for file in self.file_content:
                file.fp.seek(0)
                self.mpl_reader = MplReader(file)
                if self.mpl_reader.check():
                    break
                self.mpl_reader = None
            return True
        return False

    def prepare_tables(self):
        tables = self.mpr_reader.prepare_tables()
        while len(tables) < 12:
            self.append_table(tables)['header'].append('PLACEHOLDER')
        if self.mpl_reader:
            tables += self.mpl_reader.prepare_tables()
        return tables


Readers.instance().register( BioLogic )
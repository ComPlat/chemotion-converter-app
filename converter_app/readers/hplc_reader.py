import logging

from binary_parser import read_chromatograms

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class HplcReader(Reader):
    """
    Reads tarballed hplc files with extension .tar.gz
    """
    identifier = 'hplc_reader'
    priority = 5

    def __init__(self, file, *tar_files):
        super().__init__(file, *tar_files)
        self.df = None
        self.temp_dir = None

    def check(self):
        """
        :return: True if it fits
        """

        if self.is_tar_ball:
            try:
                if len(self.file_content) > 1:
                    self.df = read_chromatograms(self.file_content[0].file_path)
                else:
                    return False
                return True
            except ValueError:
                pass
        return False

    def prepare_tables(self):
        tables = []

        keys = list(self.df.keys())
        waves = [x for x in keys if x.startswith('Wave')]
        waves.sort()
        time = self.df['time']
        for wave_key in waves:
            wave = self.df[wave_key]
            table = self.append_table(tables)
            kv = wave_key.split('_')
            table['metadata'][kv[0]] = str(kv[1])
            table['metadata']['AllWaves'] = str(waves)
            for i, t in enumerate(time):
                table['rows'].append([t, float(wave[i])])

            table['columns'] = [{
                'key': str(idx),
                'name': f'{value}'
            } for idx, value in enumerate(['Time', 'Wavelength'])]
        return tables


Readers.instance().register(HplcReader)

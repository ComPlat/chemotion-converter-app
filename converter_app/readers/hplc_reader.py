import logging
from pathlib import Path

import hplc as ph
import chemstation as cs
import pandas as pd

from converter_app.readers.helper.ms_helper import MsHelper
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
        self.internal_name = "chemstation"

    def check(self):
        """
        :return: True if it fits
        """

        if self.is_tar_ball:
            try:
                if len(self.file_content) > 1:
                    self.df = ph.read_chromatograms(self.file_content[0].file_path)
                else:
                    return False
                return True

            except ValueError:
                return False

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

            # look and check if MS is included in folder
        try:
            mypath = self.find_ms(self.file_content[0].file_path)
            if mypath is not None:
                df_ms = cs.read_chemstation_file(str(mypath))
            else:
                df_ms = []
        except ValueError or AssertionError:
            pass
        else:
            df_ms = [df_ms] if not isinstance(df_ms, list) else df_ms
            ms_tables = MsHelper.create_ms_tables(df_ms, self.internal_name)
            tables.extend(ms_tables)

        return tables

    @staticmethod
    def find_ms(path):
        base_dir = Path(path)
        # Find all files ending with .MS (case-sensitive)
        files = list(base_dir.rglob("*.MS"))
        if len(files) == 0:
            return None
        return files[0]




Readers.instance().register(HplcReader)

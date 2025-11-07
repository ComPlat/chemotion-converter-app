import logging
from pathlib import Path

import hplc as ph
import chemstation as cs
import pandas as pd

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
                    self.df = ph.read_chromatograms(self.file_content[0].file_path)
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
            for index, spectrum in enumerate(df_ms):
                table = self.append_table(tables)
                if len(df_ms) <= 1:
                    index = -1
                self.dataframe_to_ui(index, spectrum, table, "mass spectrum - all RTimes")

                # column names normalized
                icol = 'intensities' if 'intensities' in spectrum.columns else 'intensity'
                tcol = 'time' if 'time' in spectrum.columns else 'retention_time'

                # ensure numeric
                spectrum[icol] = pd.to_numeric(spectrum[icol], errors='coerce')
                spectrum[tcol] = pd.to_numeric(spectrum[tcol], errors='coerce')

                # group by time -> each group is one MS spectrum
                for rt, group in spectrum.groupby(tcol):
                    # group is now a time-resolved MS spectrum
                    # it contains m/z vs intensity at retention time = rt

                    # send it to UI:
                    table = self.append_table(tables)
                    self.dataframe_to_ui(index, group[['mz', icol]], table, f"ms spectrum @ {rt}")

                # MS Spectrum time --> TIC
                # compute TIC = sum of intensities per time point
                table = self.append_table(tables)
                tic = spectrum.groupby(tcol, as_index=False)[icol].sum()
                tic = tic.rename(columns={'intensities': 'TIC'})

                self.dataframe_to_ui(index, tic, table, "ms chromatogramm")



        return tables

    def dataframe_to_ui(self, index, spectrum, table, reader_type: str):
        table['metadata']['internal_reader_type'] = reader_type
        table['header'].append(reader_type)
        if index == -1:
            table['metadata']['internal_scan_direction'] = "unknown"
        if index == 0:
            table['metadata']['internal_scan_direction'] = "negativ"  # assumption
        if index == 1:
            table['metadata']['internal_scan_direction'] = "positiv"  # assumption
        table['metadata']['internal_reader_name'] = "chemstation"
        table['columns'] = [
            {'key': str(idx), 'name': str(col)}
            for idx, col in enumerate(spectrum.columns)
        ]
        table['rows'] = spectrum.values.tolist()

    def find_ms(self, path):
        base_dir = Path(path)
        # Find all files ending with .MS (case-sensitive)
        files = list(base_dir.rglob("*.MS"))
        if len(files) == 0:
            return None
        return files[0]




Readers.instance().register(HplcReader)

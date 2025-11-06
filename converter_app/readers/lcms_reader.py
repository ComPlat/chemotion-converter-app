import logging

import openlab as ol
import pandas as pd

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)

class LcmsReader(Reader):
    """
    Reads tarballed lcms files / folders with extension .tar.gz
    """
    identifier = 'lcms_reader'
    priority = 10

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
                    self.df = ol.read_ms(self.file_content[0].file_path)
                else:
                    return False
                return True

            except AssertionError:  # no cdf File in container
                return False

            except ValueError:
                return False

        return False

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)

        # Extract metadata with:
        # - key = value if only one unique, non-null string exists
        # - key[i] = value_i for multiple unique values
        mdf = ol.read_attr(self.file_content[0].file_path)

        metadata_raw = mdf.to_dict(orient='list')

        table['metadata'] = {}

        for col, values in metadata_raw.items():
            unique_vals = list(map(str, pd.Series(values).dropna().unique()))
            if len(unique_vals) == 1:
                table['metadata'][col] = unique_vals[0]
            else:
                for i, val in enumerate(unique_vals):
                    table['metadata'][f"{col}[{i}]"] = val


        # MS Spectrum m/z & time --> Intensities
        for index, spectrum in enumerate(self.df):
            table = self.append_table(tables)
            self.dataframe_to_ui(index, spectrum, table, "mass spectrum")

            # MS Spectrum time --> TIC
            # ensure columns are numeric
            table = self.append_table(tables)
            spectrum['intensities'] = pd.to_numeric(spectrum['intensities'], errors='coerce')
            spectrum['time'] = pd.to_numeric(spectrum['time'], errors='coerce')

            # compute TIC = sum of intensities per time point
            tic = spectrum.groupby('time', as_index=False)['intensities'].sum()
            tic = tic.rename(columns={'intensities': 'TIC'})

            self.dataframe_to_ui(index, tic, table, "ms chromatogramm")

        # UVVIS data
        # Read the UV/Vis DataFrame from file
        uvvis_frame = ol.read_lc(self.file_content[0].file_path)

        # Get sorted list of unique wavelengths (as float, ascending)
        unique_wavelengths = sorted(uvvis_frame['wavelength'].dropna().unique().tolist())

        for wavelength in unique_wavelengths:
            # Create a new table for this wavelength
            table = self.append_table(tables)

            # Add metadata
            table['metadata']['AllWaves'] = str(unique_wavelengths)  # store all wavelengths as list
            table['metadata']['internal_reader_type'] = "lc - uv/vis"
            table['metadata']['internal_reader_name'] = "openlab"
            table['metadata']['Wavelength'] = str(wavelength)  # current wavelength

            # Filter rows for this wavelength and drop the 'wavelength' column (already in metadata)
            filtered = uvvis_frame[uvvis_frame['wavelength'] == wavelength].drop(columns='wavelength')

            # Define table columns (with index and name for each column)
            table['columns'] = [
                {'key': str(idx), 'name': str(col)}
                for idx, col in enumerate(filtered.columns)
            ]

            # Store data rows as list of lists (no column names)
            table['rows'] = filtered.values.tolist()

        return tables

    def dataframe_to_ui(self, index, spectrum, table, reader_type: str):
        table['metadata']['internal_reader_type'] = reader_type
        if index == 0:
            table['metadata']['internal_scan_direction'] = "negativ"  # defined by read_ms fkt
        if index == 1:
            table['metadata']['internal_scan_direction'] = "positiv"  # defined by read_ms fkt
        table['metadata']['internal_reader_name'] = "openlab"
        table['columns'] = [
            {'key': str(idx), 'name': str(col)}
            for idx, col in enumerate(spectrum.columns)
        ]
        table['rows'] = spectrum.values.tolist()


Readers.instance().register(LcmsReader)

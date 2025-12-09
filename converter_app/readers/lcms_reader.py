import logging

import openlab as ol
import pandas as pd

from converter_app.readers.helper.ms_helper import MsHelper
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
        self.internal_name = "openlab"

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

            ms_tables = MsHelper.create_ms_tables(self.df, self.internal_name)
            tables.extend(ms_tables)

        return tables


Readers.instance().register(LcmsReader)

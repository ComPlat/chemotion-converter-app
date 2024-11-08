import logging
import os
import shutil
import tempfile
import tarfile
import hplc as ph
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class HplcReader(Reader):
    """
    Reads tarballed hplc files with extension .tar.gz
    """
    identifier = 'hplc_reader'
    priority = 5

    def __init__(self, file):
        super().__init__(file)
        self.df = None
        self.temp_dir = None

    def check(self):
        """
        :return: True if it fits
        """
        result = self.file.name.endswith(".gz") or self.file.name.endswith(".xz") or self.file.name.endswith(".tar")
        if result:
            with  tempfile.TemporaryDirectory() as temp_dir:
                self.temp_dir = temp_dir
            with tempfile.NamedTemporaryFile(delete=True) as temp_pdf:
                try:
                    # Save the contents of FileStorage to the temporary file
                    self.file.fp.save(temp_pdf.name)
                    if self.file.name.endswith(".gz"):
                        mode = "r:gz"
                    elif self.file.name.endswith(".xz"):
                        mode = "r:xz"
                    elif self.file.name.endswith(".tar"):
                        mode = "r:"
                    else:
                        return False
                    with tarfile.open(temp_pdf.name, mode) as tar:
                        tar.extractall(self.temp_dir)
                        tar.close()

                    for p in os.listdir(self.temp_dir):
                        file_path = os.path.join(self.temp_dir, p)
                        self.df = ph.read_chromatograms(file_path)
                        break
                except ValueError:
                    return False
        if not result and self.temp_dir is not None and os.path.exists(self.temp_dir) and os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        return result

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

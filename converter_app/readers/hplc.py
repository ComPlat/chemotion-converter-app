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
        result = self.file.name.endswith(".tar.gz") or self.file.name.endswith(".tar")
        if result:
            with  tempfile.TemporaryDirectory() as temp_dir:
                self.temp_dir = temp_dir.name
            with tempfile.NamedTemporaryFile(delete=True) as temp_pdf:
                try:
                    # Save the contents of FileStorage to the temporary file
                    self.file.fp.save(temp_pdf.name)
                    if self.file.name.endswith("tar.gz"):
                        mode = "r:gz"
                    elif self.file.name.endswith("tar"):
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
        table = self.append_table(tables)

        keys = list(self.df.keys())
        values = [self.df[x] for x in keys]
        for i in range(len(values[0])):
            table['rows'].append([])
            for x in values:
                table['rows'][-1].append(float(x[i]))

        table['columns'] = [{
            'key': str(idx),
            'name': f'{value}'
        } for idx, value in enumerate(keys)]
        return tables


Readers.instance().register(HplcReader)

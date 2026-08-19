import logging
import os.path
import shutil
import subprocess as sp
import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers
from converter_app.readers.mzml import MSXmlReader

logger = logging.getLogger(__name__)


class MsRawReader(Reader):
    """
    Reader uses MS raw files using the MS_CONVERTER
    """
    identifier = 'ms_raw_reader'
    priority = 10

    def __init__(self, file):
        super().__init__(file)
        self._xml_table = []
        self.folder_name = None
        self.converted_name = None
        self.uuid_str = ''
        self._file_name = ''

    def check(self):
        """
        :return: True if it fits
        """
        result = False
        if self.file.suffix.lower() == '.raw' and self.file.encoding == 'binary':
            result = True
            self._file_name = self.file.name
            self.converted_name = Path(self.file.name).with_suffix('.mzML').name
            self.uuid_str = str(uuid.uuid4())
            in_folder_name = Path('./MS Temp Files') / self.uuid_str
            self.folder_name = in_folder_name / 'out'
            os.makedirs(self.folder_name)
            with open(in_folder_name / self.file.name, 'wb+') as f:
                f.write(self.file.content)


        if self.file.is_tar_archive:
            zip_root = Path(self.file.get_temp_dir()) / self.file.name
            file_list = [item for item in zip_root.iterdir()]
            if len(file_list) == 1 and file_list[0].suffix.lower() == '.d':
                d_folder = file_list[0]
                result = True
                self._file_name = d_folder.name
                self._file_name = d_folder.name
                self.converted_name = Path(d_folder.name).with_suffix('.mzML').name
                self.uuid_str = str(uuid.uuid4())
                in_folder_name = Path('./MS Temp Files') / self.uuid_str
                self.folder_name = in_folder_name / 'out'
                shutil.copytree(d_folder.parent, in_folder_name)
                os.makedirs(self.folder_name)

        if result:
            try:
                res = sp.run(
                    ["docker", "exec", "msconvert_docker", "wine", "msconvert", f"/data/{self.uuid_str}/{self._file_name}", "-o",
                     f"/data/{self.uuid_str}/out", "--32", "--zlib", "--filter", "peakPicking true 1-", "--filter",
                     "zeroSamples removeExtra", "--ignoreUnknownInstrumentError"], check=True)
                if res.returncode != 0:
                    return False
                return True

            except sp.CalledProcessError:
                return False
            except:
                return False

        return result

    def prepare_tables(self) -> list:
        """
        Abstract method converts the content of a file.
        """
        try:
            self._pre_prepare_tables(self.folder_name / self.converted_name)
        finally:
            shutil.rmtree(self.folder_name)
        return self._xml_table

    def _pre_prepare_tables(self, tmp_file_name):
        with open(tmp_file_name, 'rb') as f:
            content_type = "application/octet-stream"

            fs = FileStorage(stream=f, filename=tmp_file_name,
                             content_type=content_type)
            xml_file = File(fs)

            xml_reader = MSXmlReader(xml_file)
            xml_reader.check()
            self._xml_table = xml_reader.prepare_tables_from_xml(tmp_file_name)


Readers.instance().register(MsRawReader)

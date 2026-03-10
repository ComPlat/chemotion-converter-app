import logging
import os.path
import tempfile
import xml.etree.ElementTree as ET
import subprocess as sp
import requests
from flask import current_app
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

    def check(self):
        """
        :return: True if it fits
        """
        result = False

        if self.file.suffix.lower() == '.raw' and self.file.encoding == 'binary':

            try:
                with open(f'./MS Temp Files/{self.file.name}', 'wb+') as f:
                    f.write(self.file.content)
                res = sp.run(f'docker exec msconvert_docker wine msconvert /data/{self.file.name} -o /data --32 --zlib --filter "peakPicking true 1-" --filter "zeroSamples removeExtra" --ignoreUnknownInstrumentError')
                if res.returncode != 0:
                    return False
            except sp.CalledProcessError:
                return False

        return result

    def prepare_tables(self) -> list:
        """
        Abstract method converts the content of a file.
        """

        return self._xml_table

    def _pre_prepare_tables(self, mz_xml_content):
        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_file_name = os.path.join(tmpdirname, os.path.basename(self.file.name) + '.mzML')
            with open(tmp_file_name, 'wb+') as f:
                f.write(mz_xml_content)
            with open(tmp_file_name, 'rb') as f:
                content_type = "application/octet-stream"

                fs = FileStorage(stream=f, filename=tmp_file_name,
                                 content_type=content_type)
                xml_file = File(fs)

                xml_reader = MSXmlReader(xml_file)
                xml_reader.check()
                self._xml_table = xml_reader.prepare_tables()


Readers.instance().register(MsRawReader)

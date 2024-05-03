import logging
import zipfile
import defusedxml.ElementTree as ET
from converter_app.readers.helper.reader import Readers
from converter_app.readers.helper.base import Reader

logger = logging.getLogger(__name__)


class BrmlReader(Reader):
    """
    Reader for BRML files
    """
    identifier = 'brml_reader'
    priority = 10

    def check(self):
        """
        :return: True if it fits
        """
        return self.file.suffix == '.brml'

    def prepare_tables(self):
        tables = []

        with zipfile.ZipFile(self.file.fp) as zf:
            # open DataContainer.xml
            with zf.open('Experiment0/DataContainer.xml') as dc:
                data_container = ET.fromstring(dc.read())
                for raw_data in data_container.findall('./RawDataReferenceList/string'):
                    raw_data_file_name = raw_data.text

                    if raw_data_file_name in zf.namelist():
                        with zf.open(raw_data_file_name) as rd:
                            raw_data = ET.fromstring(rd.read())

                            for data_route in raw_data.findall('./DataRoutes/DataRoute'):
                                table = self.append_table(tables)


                                for datum in data_route.findall('./Datum'):
                                    row = datum.text.split(',')

                                    table['rows'].append(row)
                    else:
                        print(f"The file '{raw_data_file_name}' does not exist.")
        return tables


Readers.instance().register(BrmlReader)

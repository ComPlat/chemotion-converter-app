import os
import tempfile
import xml.etree.ElementTree as ET

import pymzml
import requests
from flask import current_app
from numpy import ndarray

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers


class MSXmlReader(Reader):
    """Extents the .mzML XML reader to decode binary analyses data"""

    identifier = 'mzml_reader'
    priority = 8

    data = ['i', 'mz']
    data_2 = ['t_mz_set','transformed_mz_with_error' ]
    ignore_fields = [None, '', 'obo_translator', 'transformed_peaks']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mz_xml_content = b''

    def check(self):
        """
        :return: True if it fits
        """

        if self.file.suffix.lower() == '.mzml':
            try:
                parsed_url = current_app.config.get('MS_CONVERTER')
            except RuntimeError:
                parsed_url = 'http://127.0.0.1:5050/'

            try:
                files = {
                    "main_file": (self.file.name, self.file.content, "application/octet-stream")
                }

                res = requests.post(parsed_url + 'fileconvert_conversion', data={'test': ''}, files=files,
                                    timeout=(5, 60))
            except requests.exceptions.ConnectionError:
                return False

            if res.status_code == 200:
                try:
                    self._mz_xml_content = res.content
                    return True
                except ET.ParseError:
                    return False

        return False


    def prepare_tables(self):
        """
        Run file conversion

        :return: Converted table object
        """

        with tempfile.TemporaryDirectory() as tmpdirname:
            tmp_file_name = os.path.join(tmpdirname, os.path.basename(self.file.name))
            with open(tmp_file_name, 'wb+') as f:
                f.write(self._mz_xml_content)
            runs = pymzml.run.Reader(tmp_file_name, build_index_from_scratch=True)

            tables = []
            table = self.append_table(tables)

            self._extract_meta_data(runs, table)
            for run in runs:
                table = self.append_table(tables)
                table['header'].append('-')
                d = self._extract_meta_data(run, table)

                def add_data_table(table, data_set, d):
                    table['columns'] = []
                    for col_idx, data_key in enumerate(data_set):

                        for idx, val in enumerate(d[data_key]):
                            while len(table['rows']) <= idx:
                                table['rows'].append([])
                            table['rows'][idx].append(str(val))
                        table['columns'].append({'key': str(col_idx), 'name': data_key})

                add_data_table(table, self.data, d)
                table = self.append_table(tables)
                table['header'].append(f'ID - {d["ID"]}')
                add_data_table(table, self.data_2, d)

            return tables

    def _extract_meta_data(self, run, table):
        d = {k: getattr(run, k, '') for k in run.__dir__() if
             k[:1] != '_' and type(getattr(run, k, '')).__name__ != 'method'}
        for key, val in d.items():
            if key not in self.data + self.data_2 + self.ignore_fields:
                if isinstance(val, ndarray):
                    table.add_metadata(key, str(val.tolist()))
                elif isinstance(val, dict):
                    self._reade_meta_data_dict(key, table, val)
                elif isinstance(val, tuple):
                    for attrib_key, attrib_val in enumerate(val):
                        table.add_metadata(key + '.' + str(attrib_key), str(attrib_val))
                elif isinstance(val, ET.Element):
                    table.add_metadata(key + '.tag', str(val.tag))
                    if val.text is not None:
                        table.add_metadata(key + '.text', val.text.strip())
                    for attrib_key, attrib_val in val.attrib.items():
                        table.add_metadata(key + '.' + attrib_key, str(attrib_val))
                else:
                    table.add_metadata(key, str(val))
        return d

    def _reade_meta_data_dict(self, key, table, val):
        for attrib_key, attrib_val in val.items():
            if isinstance(attrib_val, dict):
                for attrib_key_i, attrib_val_i in attrib_val.items():
                    table.add_metadata(key + '.' + str(attrib_key) + '.' + str(attrib_key_i), str(attrib_val_i))
            else:
                table.add_metadata(key + '.' + str(attrib_key), str(attrib_val))


Readers.instance().register(MSXmlReader)

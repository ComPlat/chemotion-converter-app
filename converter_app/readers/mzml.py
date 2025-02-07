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

    data = ['i', 'mz', 't_mz_set','transformed_mz_with_error' ]
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
            for run in runs:
                self.append_table(tables)

            self._extract_meta_data(runs, tables[0])
            tables[0].add_metadata('__IDENTIFIER', self.__class__.identifier)
            for i, run in enumerate(runs):
                table = tables[i]
                table['header'].append('-')
                d = self._extract_meta_data(run, table)


                table['rows'] = d['centroidedPeaks'].tolist()
                table['columns'].append({'key': '0', 'name': 'mz'})
                table['columns'].append({'key': '1', 'name': 'i'})

            return tables

    def _extract_meta_data(self, run, table):
        d = {k: getattr(run, k, '') for k in run.__dir__() if
             k[:1] != '_' and type(getattr(run, k, '')).__name__ != 'method'}
        for key, val in d.items():
            if key not in self.data + self.ignore_fields:
                if isinstance(val, ndarray):
                    pass #table.add_metadata(key, str(val.tolist()))
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

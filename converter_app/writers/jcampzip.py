import hashlib
import io
import json
import logging
import zipfile

from .base import Writer
from .jcamp import JcampWriter

logger = logging.getLogger(__name__)


class JcampZipWriter(Writer):

    suffix = '.zip'
    mimetype = 'application/zip'

    def __init__(self, converter):
        super().__init__(converter)
        self.profile = converter.profile
        self.matches = converter.matches
        self.zipbuffer = io.BytesIO()

    def process(self):
        metadata = {
            'profileId': self.profile.id,
            'ols': self.profile.data.get('ols'),
            'matches': self.matches,
            'tablesCount': 0,
            'tables': []
        }

        sha_strings = {'256': [], '512': []}

        with zipfile.ZipFile(self.zipbuffer, 'w') as zf:

            jc = JcampWriter(self._converter)
            for idx, tables in enumerate(jc.process_ntuples_tables()):
                file_name = f'data/table_NTUPLES{idx}.jdx'
                string = self._add_table_to_zip(metadata, tables[0], file_name, zf, jc)
                self._update_sha_strings(sha_strings, string, file_name)

            for table_id, table in enumerate([t for t in self.tables if t.get('header', {}).get('DATA CLASS') != 'NTUPLES']):
                file_name = f'data/table_{(table_id + 1):02d}.jdx'
                jc = JcampWriter(self._converter)
                jc.process_table(table)
                string = self._add_table_to_zip(metadata, table, file_name, zf, jc)
                self._update_sha_strings(sha_strings, string, file_name)

            metadata_file_name = 'metadata/converter.json'
            metadata_string = json.dumps(metadata, indent=2)
            self._update_sha_strings(sha_strings, metadata_string, metadata_file_name)
            zf.writestr(metadata_file_name, metadata_string)

            # write bagit files (https://tools.ietf.org/id/draft-kunze-bagit-16.html)
            zf.writestr('bagit.txt', 'BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n')
            zf.writestr('manifest-sha256.txt', '\n'.join(sha_strings['256']))
            zf.writestr('manifest-sha512.txt', '\n'.join(sha_strings['512']))


    def _update_sha_strings(self, sha_strings: dict[str, list[str]], content:str, filename: str):
        sha_strings['256'].append(f'{hashlib.sha256(content.encode()).hexdigest()} {filename}')
        sha_strings['512'].append(f'{hashlib.sha512(content.encode()).hexdigest()} {filename}')

    def _add_table_to_zip(self, metadata, table, file_name, zf, jc):
        string = jc.write()
        zf.writestr(file_name, string)
        metadata['tablesCount'] += 1
        metadata['tables'].append({
            'fileName': file_name,
            'header': table['header']
        })
        return string

    def write(self) -> bytes | str:
        return self.zipbuffer.getvalue()

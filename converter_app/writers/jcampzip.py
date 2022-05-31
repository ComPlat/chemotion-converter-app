import io
import hashlib
import json
import zipfile
import logging

from .jcamp import JcampWriter

logger = logging.getLogger(__name__)


class JcampZipWriter(JcampWriter):

    suffix = '.zip'
    mimetype = 'application/zip'

    def __init__(self, converter):
        self.profile = converter.profile
        self.matches = converter.matches
        self.tables = converter.tables
        self.zipbuffer = io.BytesIO()

    def process(self):
        metadata = {
            'profileId': self.profile.id,
            'ols': self.profile.data.get('ols'),
            'matches': self.matches,
            'tablesCount': 0,
            'tables': []
        }

        sha256_string = ''
        sha512_string = ''

        zf = zipfile.ZipFile(self.zipbuffer, 'w')
        for table_id, table in enumerate(self.tables):
            self.buffer = io.StringIO()
            self.process_table(table)
            string = self.buffer.getvalue()

            file_name = 'data/table_{:02d}.jdx'.format(table_id + 1)
            zf.writestr(file_name, string)

            sha256_string += '{} {}\n'.format(hashlib.sha256(string.encode()).hexdigest(), file_name)
            sha512_string += '{} {}\n'.format(hashlib.sha512(string.encode()).hexdigest(), file_name)

            metadata['tablesCount'] += 1
            metadata['tables'].append({
                'fileName': file_name,
                'header': table['header']
            })

        metadata_file_name = 'metadata/converter.json'
        metadata_string = json.dumps(metadata, indent=2)
        sha256_string += '{} {}\n'.format(hashlib.sha256(metadata_string.encode()).hexdigest(), metadata_file_name)
        sha512_string += '{} {}\n'.format(hashlib.sha512(metadata_string.encode()).hexdigest(), metadata_file_name)
        zf.writestr(metadata_file_name, metadata_string)

        # write bagit files (https://tools.ietf.org/id/draft-kunze-bagit-16.html)
        zf.writestr('bagit.txt', 'BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n')
        zf.writestr('manifest-sha256.txt', sha256_string)
        zf.writestr('manifest-sha512.txt', sha512_string)

        # close zip file
        zf.close()

    def write(self):
        return self.zipbuffer.getvalue()

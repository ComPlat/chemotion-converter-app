import io
import hashlib
import json
import zipfile

from .jcamp import JcampWriter


class JcampZipWriter(JcampWriter):

    suffix = '.zip'
    mimetype = 'application/zip'

    def __init__(self):
        self.zipbuffer = io.BytesIO()

    def process(self, tables):
        headers = {
            'count': 0,
            'headers': []
        }

        sha256_string = ''
        sha512_string = ''

        zf = zipfile.ZipFile(self.zipbuffer, 'w')
        for table_id, table in enumerate(tables):
            self.buffer = io.StringIO()
            self.process_table(table)
            string = self.buffer.getvalue()

            file_name = 'data/table_{:02d}.jdx'.format(table_id + 1)
            zf.writestr(file_name, string)

            sha256_string += '{} {}\n'.format(hashlib.sha256(string.encode()).hexdigest(), file_name)
            sha512_string += '{} {}\n'.format(hashlib.sha512(string.encode()).hexdigest(), file_name)

            headers['count'] += 1
            headers['headers'].append({
                key.upper(): value for key, value in table['header'].items()
            })

        headers_file_name = 'metadata/headers.json'
        headers_string = json.dumps(headers, indent=2)
        sha256_string += '{} {}\n'.format(hashlib.sha256(headers_string.encode()).hexdigest(), headers_file_name)
        sha512_string += '{} {}\n'.format(hashlib.sha512(headers_string.encode()).hexdigest(), headers_file_name)
        zf.writestr(headers_file_name, headers_string)

        # write bagit files (https://tools.ietf.org/id/draft-kunze-bagit-16.html)
        zf.writestr('bagit.txt', 'BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n')
        zf.writestr('manifest-sha256.txt', sha256_string)
        zf.writestr('manifest-sha512.txt', sha512_string)

        # close zip file
        zf.close()

    def write(self):
        return self.zipbuffer.getvalue()

import hashlib
import io
import json
import logging
import tempfile
import zipfile

from converter_app.writers.rdf import RDFWriter

from converter_app.writers.base import Writer
from converter_app.writers.jcamp import JcampWriter

logger = logging.getLogger(__name__)


class JcampZipWriter(Writer):
    suffix = '.zip'
    mimetype = 'application/zip'

    def __init__(self, converter):
        super().__init__(converter)
        self.profile = converter.profile
        self.matches = converter.get_matches(dataset=True)
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

        zf = zipfile.ZipFile(self.zipbuffer, 'w')


        for (attachment_file, filename, file_type) in self.converter.attachments:
            file_path = f'attachments/{filename}'
            with tempfile.NamedTemporaryFile(delete=True) as temp:
                temp.write(attachment_file)
                zf.write(temp.name, file_path)

                sha256_string += '{} {}\n'.format(hashlib.sha256(attachment_file).hexdigest(), file_path)
                sha512_string += '{} {}\n'.format(hashlib.sha512(attachment_file).hexdigest(), file_path)

        for table_id, table in enumerate(self.tables):
            self.buffer = io.StringIO()
            self.process_table(table)
            string = self.buffer.getvalue()
        with zipfile.ZipFile(self.zipbuffer, 'w') as zf:

            rdf_writer = RDFWriter(self._converter)

            file_name = f'metadata/rdf.ttl'
            rdf_writer.process()
            rdf_result = rdf_writer.write()
            self._update_sha_binary(sha_strings, rdf_result, file_name)
            zf.writestr(file_name, rdf_result.decode())
            rv_matches = self._converter.get_reaction_variation_matches()
            if rv_matches['samples']:
                reaction_variation_file_name = 'metadata/reaction_variation.json'
                reaction_variation = json.dumps(rv_matches, indent=2)
                self._update_sha_strings(sha_strings, reaction_variation, reaction_variation_file_name)
                zf.writestr(reaction_variation_file_name, reaction_variation)

            jc = JcampWriter(self._converter)
            for idx, header in enumerate(jc.process_ntuples_tables()):
                file_name = f'data/table_NTUPLES{idx}.jdx'
                binary_string = self._add_table_to_zip(metadata, header, file_name, zf, jc)
                self._update_sha_binary(sha_strings, binary_string, file_name)

            for table_id, table in enumerate(
                    [t for t in self.tables if not isinstance(t, list)]):
                file_name = f'data/table_{(table_id + 1):02d}.jdx'
                jc = JcampWriter(self._converter)
                jc.process_table(table)
                binary_string = self._add_table_to_zip(metadata, table['header'], file_name, zf, jc)
                self._update_sha_binary(sha_strings, binary_string, file_name)

            metadata_file_name = 'metadata/converter.json'
            metadata_string = json.dumps(metadata, indent=2)
            self._update_sha_strings(sha_strings, metadata_string, metadata_file_name)
            zf.writestr(metadata_file_name, metadata_string)

            # write bagit files (https://tools.ietf.org/id/draft-kunze-bagit-16.html)
            zf.writestr('bagit.txt', 'BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n')
            zf.writestr('manifest-sha256.txt', '\n'.join(sha_strings['256']))
            zf.writestr('manifest-sha512.txt', '\n'.join(sha_strings['512']))

    def _update_sha_strings(self, sha_strings: dict[str, list[str]], content: str, filename: str):
        sha_strings['256'].append(f'{hashlib.sha256(content.encode()).hexdigest()} {filename}')
        sha_strings['512'].append(f'{hashlib.sha512(content.encode()).hexdigest()} {filename}')

    def _update_sha_binary(self, sha_strings: dict[str, list[str]], content: bytes, filename: str):
        sha_strings['256'].append(f'{hashlib.sha256(content).hexdigest()} {filename}')
        sha_strings['512'].append(f'{hashlib.sha512(content).hexdigest()} {filename}')

    def _add_table_to_zip(self, metadata, header, file_name, zf, jc):
        string = jc.write()
        zf.writestr(file_name, string)
        metadata['tablesCount'] += 1
        metadata['tables'].append({
            'fileName': file_name,
            'header': header
        })
        return string

    def write(self) -> bytes:
        return self.zipbuffer.getvalue()

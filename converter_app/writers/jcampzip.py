import io
import zipfile

from .jcamp import JcampWriter


class JcampZipWriter(JcampWriter):

    suffix = '.zip'
    mimetype = 'application/zip'

    def __init__(self):
        self.zipbuffer = io.BytesIO()

    def process(self, tables):
        zf = zipfile.ZipFile(self.zipbuffer, 'w')
        for table_id, table in enumerate(tables):
            self.buffer = io.StringIO()
            self.process_table(table)

            file_name = 'Table_{:02d}.jdx'.format(table_id + 1)
            zf.writestr(file_name, self.buffer.getvalue())

            # close zip file
        zf.close()

    def write(self):
        return self.zipbuffer.getvalue()

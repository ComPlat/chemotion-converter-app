import os
import shutil
import tempfile

from gcode_translator.GCode_Translator import use

from converter_app.readers import Readers
from converter_app.readers.helper.base import Reader, AttachmentType


class GCodeReader(Reader):
    """
    Reads gcode files with extension .gcode, .gx and .bgcode
    """
    identifier = 'gcode_reader'
    priority = 5

    def check(self):
        """
        :return: True if it fits
        """
        return self.file.suffix in ('.gcode', '.gx', '.bgcode')

    def prepare_tables(self):
        tables = []

        # use() needs a path on disk, so dump the uploaded content into a temp file
        # keeping the original suffix (use() dispatches on the extension). For .bgcode
        # the native binary writes the converted .gcode next to it, hence a dedicated
        # temp directory that we remove as a whole afterwards.
        tmp_dir = tempfile.mkdtemp()
        try:
            tmp_path = os.path.join(tmp_dir, f'input{self.file.suffix}')
            with open(tmp_path, 'wb') as tmp:
                tmp.write(self.file.content)

            # use() orchestrates the whole pipeline: .bgcode -> .gcode conversion,
            # .gx thumbnail extraction + text-offset skipping, per-line translation
            # and aggregation. It returns the sorted/filtered [g_dict, m_dict, other_dict]
            # and the embedded preview image(s) as raw bytes (decoded in memory).
            result, previews = use(
                file=tmp_path,
                lists_to_strings=True,
                mapping_source='local',
                return_preview=True,
            )
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        for values in result:
            table = self.append_table(tables)
            table['metadata'] = values

        if previews:
            preview = previews[0]
            if preview.startswith(b'\x89PNG\r\n\x1a\n'):
                self.add_attachment(preview, 'preview.png', AttachmentType.PNG)
            elif preview.startswith(b'BM'):
                self.add_attachment(preview, 'preview.bmp', AttachmentType.BMP)

        return tables


Readers.instance().register(GCodeReader)

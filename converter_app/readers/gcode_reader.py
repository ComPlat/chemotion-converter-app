import re
import tempfile
import os

from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers import Readers
from converter_app.readers.helper.base import Reader
# from converter_app.readers.helper.g_code_translator_package.Binary_GCode_Translator import \
    # extract_picture_bytes_from_content, binary_gcode_to_gcode
# from converter_app.readers.helper.g_code_translator_package.GCode_Translator import GCodeTranslator

from gcode_translator.GCode_Translator import GCodeTranslator
from gcode_translator.Binary_GCode_Translator import binary_gcode_to_gcode, extract_picture_bytes_from_content


class GCodeReader(Reader):
    """
    Reads gcode files with extension .gcode, .gx and .bgcode
    """
    identifier = 'gcode_reader'
    priority = 5

    def __init__(self, file, *tar_content):
        super().__init__(file, tar_content)
        self._out = None
        self.tmp_path = None

    def check(self):
        """
        :return: True if it fits
        """
        return self.file.suffix == '.gcode' or self.file.suffix == '.gx' or self.file.suffix == '.bgcode'

    def prepare_tables(self):
        tables = []
        image_data = None

        translator = GCodeTranslator()
        gcode_mapping = translator.init_mapping("local")



        if self.file.suffix == '.bgcode':
            with tempfile.NamedTemporaryFile(delete=False, suffix=".bgcode") as tmp:
                tmp.write(self.file.content)
                self.tmp_path = tmp.name
                # print("Starting C++ EXE...")
                self._out = binary_gcode_to_gcode(self.tmp_path)
                f = open(self._out, 'rb')
                fs = FileStorage(stream=f, filename=self._out,
                                 content_type="text/plain")
                self.file = File(fs)
            # print("...Finished C++ EXE")

        if self.file.suffix == '.gx':
            image_data, remaining_data = extract_picture_bytes_from_content(self.file.content)
            encoding = self.file.encoding

            if encoding.lower() == "binary" or encoding not in ["utf-8", "latin-1", "ascii"]:
                encoding = "utf-8"  # fallback

            all_lines = re.split(r'[\r\n]+', remaining_data.decode(encoding))
        else: # normal .gcode case or after transformation from bgcode to gcode
            all_lines = re.split(r'[\r\n]+', self.file.content.decode(self.file.encoding)) # for file line only ends with \r and not with \n

        table = self.append_table(tables)
        for line in all_lines:
            line = line.rstrip()
            result, in_header = translator.explain_gcode_line(line, gcode_mapping, True, False)
            if in_header:
                table["header"].append(result)
            else:
                translator.translated_line_to_dict(result)
                match = re.match(r';\s*([^:]+):(.+)', line)
                if match:
                    table['metadata'][match.group(1)] = match.group(2)
        translator.clean_str_from_dict()
        for values in translator.sort_and_filter_dict(True):
            table = self.append_table(tables)
            table['metadata'] = values
        if not image_data:
            image_data = translator.get_preview_as_stream()
        if image_data:
            self.attachment_files.append({'preview.png': image_data})

        return tables

    def __del__(self):
        if self._out and os.path.exists(self._out):
            os.remove(self._out)
        if self.tmp_path and os.path.exists(self.tmp_path):
            os.remove(self.tmp_path)


Readers.instance().register(GCodeReader)
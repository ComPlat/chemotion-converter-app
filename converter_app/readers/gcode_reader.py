import re

from converter_app.readers import Readers
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.g_code_translator_package.GCode_Translator import GCodeTranslator


class GCodeReader(Reader):
    """
    Reads gcode files with extension .gcode
    """
    identifier = 'gcode_reader'
    priority = 5

    def check(self):
        """
        :return: True if it fits
        """
        return self.file.suffix == '.gcode'

    def prepare_tables(self):
        tables = []

        translator = GCodeTranslator()
        gcode_mapping = translator.init_mapping()

        all_lines = re.split(r'[\r\n]+', self.file.content.decode(self.file.encoding)) # for file line only ends with \r and not with \n

        table = self.append_table(tables)
        for line in all_lines:
            line = line.rstrip()
            result = translator.explain_gcode_line(line, gcode_mapping, True, True)
            translator.translated_line_to_dict(result)
            match = re.match(r';\s*([^:]+):(.+)', line)
            if match:
                table['metadata'][match.group(1)] = match.group(2)
        translator.clean_str_from_dict()
        for values in translator.sort_and_filter_dict(True):
            table = self.append_table(tables)
            table['metadata'] = values # TODO: GCode comments as header
            table["header"].append("Test")
        image_data = translator.get_preview_as_stream()
        if image_data:
            self.attachment_files.append({'preview.png': image_data})

        return tables


Readers.instance().register(GCodeReader)
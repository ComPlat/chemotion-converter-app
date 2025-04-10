import base64

import converter_app.readers.helper.g_code_translator_package.helper as helper
from converter_app.readers.helper.g_code_translator_package.GCode_Mapping import MarlinGcodeScraper, GCode_Mapping, GCodeFlavor
from typing import Dict


class GCodeTranslator:
    def __init__(self):
        self.line_is_a_picture = False
        self.picture_code = []
        self.output_dict = {}
        print("Initializing GCode Translator")

    def init_mapping(self):
        scraper = GCode_Mapping()
        if scraper.gcode_type == GCodeFlavor.GENERIC or scraper.gcode_type == GCodeFlavor.MARLIN:
            scraper = MarlinGcodeScraper()
        mapping = {}  # initialize as valid empty dic
        try:
            mapping = scraper.fetch_gcode_mapping()
        except Exception as e:
            print("❌ Failed to fetch G-code mapping:", e)
        finally:
            scraper.close()
        return mapping

    def explain_gcode_line(self, line_to_translate, mapping, preview_picture_needed=True, preview_pic_as_file=True):
        if line_to_translate.startswith("; thumbnail end"):
            self.line_is_a_picture = False
            if preview_picture_needed and preview_pic_as_file:
                self.transform_preview_picture()
            return ""
        if line_to_translate.startswith("; thumbnail begin") or self.line_is_a_picture:
            if not self.line_is_a_picture:
                self.picture_code = []
                self.line_is_a_picture = True
            if preview_picture_needed:
                self.extract_preview_picture(line_to_translate)
            return ""
        if line_to_translate.startswith(";") or line_to_translate.strip() == "":
            return line_to_translate

        parts = line_to_translate.strip().split()
        cmd = parts[0]
        params = parts[1:]

        if mapping is not None:
            explanation = mapping.get(cmd, "Unknown command")
            param_str = "True" if not params else " ".join(params)
            if param_str == "True":
                print(f"{cmd}: {explanation} | Parameter: {param_str}")
            return f"{cmd}: {explanation} | Parameter: {param_str}"
        else:
            param_str = "True" if not params else " ".join(params)
            return f"{cmd}: Unknown mapping | Parameter: {param_str}"

    def translated_line_to_dict(self, translated_line):
        if "|" in translated_line:
            cmd = translated_line.split("|")[0].strip()
            comment_hint = translated_line.split(";")[-1].strip() if ";" in translated_line else ""
            if "Unknown command" in cmd and comment_hint:
                cmd = cmd.replace("Unknown command", "Special command - " + comment_hint)
            params = translated_line.split("|")[1].split(";")[0].strip(' ,\t\n')
            if "Parameter:" in params:
                param_parts = params.split(":", 1)
                if len(param_parts) == 2 and param_parts[1].strip() == "":
                    params += " True"
            helper.add_to_dict_smart(self.output_dict, cmd, params)

    def clean_str_from_dict(self, string_to_clean="Parameter:"):
        """
        Removes a given substring from all values in the output_dict.
        Works for both string values and lists of strings.

        :param string_to_clean: The substring to remove from all values
        """
        for key in self.output_dict:
            value = self.output_dict[key]

            if isinstance(value, str):
                # Clean substring from string
                self.output_dict[key] = value.replace(string_to_clean, "").strip()

            elif isinstance(value, list):
                # Clean substring from each element in the list
                cleaned_list = [
                    v.replace(string_to_clean, "").strip() if isinstance(v, str) else v
                    for v in value
                ]
                self.output_dict[key] = cleaned_list

    def sort_and_filter_dict(self, lists_to_strings=False, should_sort=True, should_filter=True):
        if should_sort:
            # noinspection PyUnusedLocal
            def my_gcode_sort_key(key_: str):
                # inner function to extract sortable key
                prefix = key_[0]
                number = int(''.join(filter((lambda c: c.isdigit()), key_)))
                return prefix, number

            self.output_dict = dict(sorted(self.output_dict.items(), key=lambda item: my_gcode_sort_key(item[0])))

        if should_filter:
            g_dict = {}
            m_dict = {}
            other_dict = {}
            for key, value in self.output_dict.items():
                if key.startswith("G"):
                    g_dict[key] = str(value) if lists_to_strings else value
                elif key.startswith("M"):
                    m_dict[key] = str(value) if lists_to_strings else value
                else:
                    other_dict[key] = str(value) if lists_to_strings else value

            return [g_dict, m_dict, other_dict]

        return [self.output_dict]

    def extract_preview_picture(self, line_to_translate):
        if not line_to_translate.startswith("; thumbnail"):
            self.picture_code.append(line_to_translate.lstrip("; ").strip())

    def get_preview_as_stream(self):
        if not self.picture_code:
            print("⚠️ No preview image data found.")
            return None

        base64_data = "".join(self.picture_code)
        try:
            return base64.b64decode(base64_data)
        except Exception as e:
            print(f"❌ Failed to decode preview image: {e}")
            return None

    def transform_preview_picture(self):
        image_data = self.get_preview_as_stream()
        if not image_data:
            return
        pic_name = "preview.png"
        with open(pic_name, "wb") as img_file:
            img_file.write(image_data)
        print(f"✅ Thumbnail saved as '{pic_name}'.")


if __name__ == "__main__":
    with open(r"EN4MAX_Kugelbahn.gcode") as f:
        translator = GCodeTranslator()
        gcode_mapping = translator.init_mapping()
        for line in f:
            result = translator.explain_gcode_line(line, gcode_mapping)
            # with open("output.txt", "a") as o:
            # o.write(result+"\n")
            translator.translated_line_to_dict(result)
        translator.clean_str_from_dict()
        dictList_for_converter = translator.sort_and_filter_dict(True)
        print(dictList_for_converter)

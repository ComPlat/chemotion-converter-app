import logging
import re

from converter_app.readers.helper import time_interpreter
from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class DelfinReader(Reader):
    identifier = 'deflin_reader'
    priority = 3

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self.all_lines = []
        self.atom_list = []

    def __extract_xyz(self, data):
        if isinstance(data, str):
            parts = data.strip().split()
            if len(parts) != 4:
                return  # invalid format
            atom = parts[0]
            try:
                x, y, z = map(float, parts[1:])
            except ValueError:
                return
        elif hasattr(data, "groups"):  # likely a match object
            groups = data.groups()
            if len(groups) != 4:
                return
            atom, x, y, z = groups
            try:
                x, y, z = float(x), float(y), float(z)
            except ValueError:
                return
        else:
            return  # unsupported type

        self.atom_list.append((atom, x, y, z))

    def parse_key_value_blocks(self, excluded_keys=None):
        if excluded_keys is None:
            excluded_keys = {"Coordinates"}  # add more if needed

        result = {}
        current_key = None
        value_lines = []

        for line in self.all_lines:
            stripped = line.strip()

            # If this line starts with an excluded key, finish current block and skip
            if any(stripped.startswith(key + ":") for key in excluded_keys):
                if current_key and value_lines:
                    result[current_key] = str(" -- ".join(value_lines))
                current_key = None
                value_lines = []
                continue

            # Check for a new header line like "Some Key: value"
            if match := re.match(r'^(?!#)([^:]+):\s*(.*)', stripped):
                candidate_key = match.group(1).strip()
                if candidate_key in excluded_keys:
                    continue
                # Save previous key-value block
                if current_key and value_lines:
                    result[current_key] = str(" -- ".join(value_lines))
                current_key = candidate_key
                first_value = match.group(2).strip()
                value_lines = [first_value] if first_value else []

            # Collect indented lines as value part
            elif current_key and line.strip() and (line.startswith(" ") or line.startswith("\t")):
                value_lines.append(line.strip())

        # Final key-value pair
        if current_key and value_lines:
            result[current_key] = str(" -- ".join(value_lines))

        return result

    def __write_xyz_file(self):
        raise NotImplementedError("This method is not yet implemented.")
        # return # TODO: Add attachments or file output per file writer

    def check(self):
        """
        :return: True if it fits
        """
        custom_suffix = [".delf", ".delfo", ".delfout"]
        result = self.file.suffix.lower() == '.txt' or any(self.file.suffix.lower().endswith(ext) for ext in custom_suffix)
        if result:
            self.all_lines = re.split(r'[\r\n]+', self.file.content.decode(self.file.encoding))
            result = any("DELFIN" in line for line in self.all_lines)
        return result

    def prepare_tables(self):
        tables = []
        xyz_pattern = r'^([A-Za-z]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)$'

        table = self.append_table(tables)
        table['metadata']['program'] = 'DELFIN'

        table['metadata'].update(self.parse_key_value_blocks())

        for line in self.all_lines:
            line = line.rstrip()
            if "SMILES" in line:
                continue
            if "Version" in line:
                table['metadata']["version"] = line.split()[2].strip()
            if "This program automates" in line:
                table['metadata']["target"] = line.split()[4].strip()
                table['metadata']["target version"] = line.split()[5].strip()
            if line.endswith(':'):
                table = self.append_table(tables)
                table['metadata']["block"] = line.replace(":", " ")
                table['header'].append(line[:-1])
            elif ":" in line:
                table['header'].append(line)
                if "time" in line.lower():
                    duration_in_hours = time_interpreter.time_string_to_hours(line)
                    table['metadata']['total run time [h]'] = str(duration_in_hours)
            if "=" in line:
                table['metadata'][line.split("=")[0]] = line.split("=")[1]
            if match := re.match(xyz_pattern, line.strip()):
                self.__extract_xyz(match)

        return tables

Readers.instance().register(DelfinReader)
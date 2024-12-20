import datetime
import logging
import re

from converter_app.readers.helper.base import Reader
from converter_app.readers.helper.reader import Readers

logger = logging.getLogger(__name__)


class GcdReader(Reader):
    """
    Reads GCD files with extension .txt
    """
    identifier = 'gcd_reader'
    priority = 5

    def __init__(self, file, *tar_content):
        super().__init__(file, *tar_content)
        self.lines = None

        self._number_of_ch = 0
        self._delimiter = ';'

    def _parse_input(self):
        current_header = '[NO HEADER]'
        header_re = re.compile(r'^\[.+]$')
        content = {current_header: []}
        for x in self.file.string.splitlines():
            if x != '':
                if header_re.match(x) is not None:
                    current_header = x
                    content[x] = []
                else:
                    content[current_header].append(x)
        return content

    def check(self):
        """
        :return: True if it fits
        """
        if self.is_tar_ball:
            self.file = next((x for x in self.file_content if x.name.lower().endswith('.gcd.txt')), None)
            if self.file is None:
                return False

        result = self.file.suffix.lower() == '.txt'
        if result:
            self.lines = self._parse_input()
            result = '[Chromatogram (Ch1)]' in self.lines and '[Compound Results(Ch1)]' in self.lines
        return result

    def prepare_tables(self):
        tables = []
        table = self.append_table(tables)
        time_re = re.compile(r'\d{1,2}:\d{1,2}:\d{1,2} [AP]M')
        date_re = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
        datetime_re = re.compile(fr'{date_re.pattern}\s{time_re.pattern}')
        date_read_formate = "%m/%d/%Y"
        time_read_formate = "%I:%M:%S %p"
        datetime_read_formate = f"{date_read_formate} {time_read_formate}"
        date_write_formate = "%d.%m.%Y"
        time_write_formate = "%H:%M:%S"
        datetime_write_formate = f"{date_write_formate} {time_write_formate}"
        for header_key in ['[Header]', '[File Information]', '[Sample Information]', '[Configuration]',
                           '[Original Files]']:
            table['header'].append('')
            table['header'].append(header_key)
            for line in self.lines.get(header_key, []):
                table['header'].append(line)
                key, value = [x.strip() for x in line.split(self._delimiter, 1)]
                if datetime_re.match(value) is not None:
                    value = datetime.datetime.strptime(value, datetime_read_formate).strftime(datetime_write_formate)
                if time_re.match(value) is not None:
                    value = datetime.datetime.strptime(value, time_read_formate).strftime(time_write_formate)
                if date_re.match(value) is not None:
                    value = datetime.datetime.strptime(value, date_read_formate).strftime(date_write_formate)
                if key in ['Detector ID', 'Detector Name', '# of Channels']:
                    if key == '# of Channels':
                        self._number_of_ch = sum(int(x) for x in value.split(self._delimiter))
                        table['metadata'][key] = str(self._number_of_ch)
                    for idx, val_item in enumerate(value.split(self._delimiter)):
                        table['metadata'][f'{header_key}.{key}.{idx + 1}'] = val_item
                else:
                    table['metadata'][f'{header_key}.{key}'] = value

        table['columns'] = []
        table['rows'] = []
        table['metadata']['rows'] = str(len(table['rows']))
        table['metadata']['columns'] = str(len(table['columns']))

        def add_peak_table(header, lines=None, idx=0):
            if lines is None:
                lines = self.lines[header]
            key, number_of_ids = [x.strip() for x in lines[0].split(self._delimiter, 1)]
            table = self.append_table(tables)
            table['header'] += lines
            table['metadata']['Header'] = header
            table['metadata'][key] = number_of_ids
            col_names = [x.strip() for x in lines[1].split(self._delimiter)]
            for line in lines[2:]:
                table_entries = line.split(self._delimiter)
                table['rows'].append(table_entries)
                for idx_entry, entry in enumerate(table_entries):
                    table['metadata'][f"Ch{idx + 1}.Id {table_entries[0]}.{col_names[idx_entry]}"] = entry

            table['columns'] = [{
                'key': str(idx),
                'name': value
            } for idx, value in enumerate(col_names)]

        for idx in range(self._number_of_ch):
            header = f"[Compound Results(Ch{idx + 1})]"
            add_peak_table(header, idx=idx)
            header = f"[Peak Table(Ch{idx + 1})]"
            data_lines = [x for x in self.lines[header][2:] if x.split(self._delimiter)[9].strip() != '']
            lines = self.lines[header][:2] + data_lines
            add_peak_table(header, lines=lines, idx=idx)

        def add_value_table(header):
            lines = self.lines[header]
            table = self.append_table(tables)
            table['metadata']['Header'] = header

            metas = [x for x in lines if re.match(r'^\d', x) is None]
            values = [[float(y) for y in x.split(self._delimiter)] for x in lines if re.match(r'^\d', x) is not None]
            for line in metas[:-1]:
                key, value = [x.strip() for x in line.split(self._delimiter, 1)]
                table['metadata'][f"{header}.{key}"] = value
            table['rows'] = values

            table['columns'] = [{
                'key': str(idx),
                'name': value
            } for idx, value in enumerate(metas[-1].split(self._delimiter))]

        for idx in range(self._number_of_ch):
            header = f"[Chromatogram (Ch{idx + 1})]"
            add_value_table(header)

        header = '[Status Trace (Column Oven Temperature)]'
        add_value_table(header)

        header = '[Status Trace (Injection Unit Temperature)]'
        add_value_table(header)

        header = '[Status Trace (Carrier Gas Pressure)]'
        add_value_table(header)

        header = '[Status Trace (Carrier Gas Flow)]'
        add_value_table(header)

        header = '[Status Trace (Column Flow)]'
        add_value_table(header)

        header = '[Status Trace (Linear Velocity)]'
        add_value_table(header)

        return tables


Readers.instance().register(GcdReader)

import csv
import io


from .base import Reader

class TXTReader(Reader):
    identifier = 'txt_reader'

    def check(self):
        self.file.read()
        self.file.seek(0)
        parts = []
        current_part = []
        count = 0
        while True:
            line = self.file.readline()
            if not line:
                parts.append(current_part)
                break
            else:
                if '==' in str(line):
                    if count > 0:
                        parts.append(current_part)
                    current_part = []
                current_part.append(line)
            count += 1
            self.parts = parts
        return len(parts) > 1

    def get_metadata(self):
        metadata = super().get_metadata()
        return metadata

    def convert_to_dict(self):
        cleaned_data = []
        for part in self.parts:
            part_dict = {
                'title': str(part[0]).replace(' ', '').split('==')[1],
                'data': self.process_data_part(part[1:])
            }
            cleaned_data.append(part_dict)

        return {
            'header': [],
            'data': [],
        }

    def get_table_data(self, data_part):
        header = []
        data = []
        for entry in data_part:
            is_data = True
            entry_as_table = [substr.replace('\r\n', '')
                              for substr in entry.split(' ')
                              if not substr == '']
            for point in entry_as_table:
                try:
                    float(point)
                except ValueError:
                    is_data = False
                    break
            if is_data:
                data.append(entry_as_table)
            else:
                header.append(entry)

        cols_count = data
            



    def process_data_part(self, data_part):
        processed_data = []
        is_table = True
        for entry in data_part:
            as_string = str(entry.decode("ISO-8859-1"))
            if as_string not in ['\r\n']:
                processed_data.append(as_string)
        last_line = processed_data[-1].split(' ')
        last_line_data = []
        for entry in last_line:
            if not entry == '':
                last_line_data.append(entry)
        for entry in last_line_data:
            try:
                float(entry)
            except ValueError:
                is_table = False
                break
        if is_table:
            self.get_table_data(processed_data)


        return processed_data

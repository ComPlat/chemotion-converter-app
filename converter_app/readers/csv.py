import csv
import io


from .base import Reader


class CSVReader(Reader):
    identifier = 'csv_reader'

    def check(self):
        try:
            file = self.file.read().decode('utf-8')
            io_string = io.StringIO(file)
            dialect = csv.Sniffer().sniff(
                io_string.read(1024), delimiters=";,\t")
            io_string.seek(0)
            self.reader = csv.reader(io_string, dialect)
            return True
        except (csv.Error, UnicodeDecodeError):
            return False

    def convert_to_dict(self):
        header = next(self.reader, None)
        res_header = []
        for idx, entry in enumerate(header):
            res_header.append({
                'key': str(idx),
                'name': entry.strip()
            })

        data = []
        for row in self.reader:
            row_dict = {}
            for idx, value in enumerate(row):
                row_dict[res_header[idx]['key']] = value
            data.append(row_dict)

        result = {
            'header': res_header,
            'data': data,
        }

        return result

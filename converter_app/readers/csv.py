import csv
import io

from flask import jsonify

from .base import Reader


class CSVReader(Reader):
    identifier = 'csv_reader'

    def check(self):
        return self.file.content_type == 'text/csv'

    def process(self):
        return self.test_csv()

    def test_csv(self):
        try:
            file = self.file.read().decode('utf-8')
            io_string = io.StringIO(file)
            dialect = csv.Sniffer().sniff(
                io_string.read(1024), delimiters=";,")
            io_string.seek(0)
            reader = csv.reader(io_string, dialect)
            csv_as_dict = self.convert_to_json(reader)
            return jsonify({'result': csv_as_dict}), 201
        except UnicodeDecodeError:
            return jsonify({'error': 'This is not a valid CSV File'}), 400
        except csv.Error:
            return jsonify(
                {'error': 'CSV could not be parsed.'}), 400

    def convert_to_json(self, reader):
        header = next(reader, None)

        res_header = []

        for entry in header:
            res_header.append({
                'key': entry.lower().strip(),
                'name': entry.strip()
            })

        data = []

        for row in reader:
            row_dict = {}
            for idx, value in enumerate(row):
                row_dict[res_header[idx]['key']] = value
            data.append(row_dict)

        result = {
            'header': res_header,
            'data': data
        }

        return result

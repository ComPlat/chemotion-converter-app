import csv
import io

from flask import jsonify


def convert_csv_to_json(reader):
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


def test_csv(csv_file):
    try:
        file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(file)
        dialect = csv.Sniffer().sniff(
            io_string.read(1024), delimiters=";,")
        io_string.seek(0)
        reader = csv.reader(io_string, dialect)
        csv_as_dict = convert_csv_to_json(reader)
        return jsonify({'result': csv_as_dict}), 201
    except UnicodeDecodeError:
        return jsonify({'error': 'This is not a valid CSV File'}), 400
    except csv.Error:
        return jsonify(
            {'error': 'CSV could not be parsed.'}), 400

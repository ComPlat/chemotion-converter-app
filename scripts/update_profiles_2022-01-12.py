import argparse
import json

from pathlib import Path

parser = argparse.ArgumentParser('Converts all profiles from INPUTPATH and writes them to OUTPUTPATH')
parser.add_argument('input_path')
parser.add_argument('output_path')

args = parser.parse_args()

input_path = Path(args.input_path)
output_path = Path(args.output_path)
output_path.mkdir(parents=True, exist_ok=True)

for input_file_path in input_path.iterdir():
    profile = json.load(input_file_path.open())
    profile['id'] = input_file_path.with_suffix('').name

    header = profile.get('header', {})
    table = profile.get('table', {})
    first_row_is_header = table.get('firstRowIsHeader')

    del table['firstRowIsHeader']
    del profile['header']
    del profile['table']

    profile['tables'] = [
        {
            'header': header,
            'table': table
        }
    ]
    profile['firstRowIsHeader'] = first_row_is_header

    output_file_path = output_path / input_file_path.name
    json.dump(profile, output_file_path.open('w'), indent=2)

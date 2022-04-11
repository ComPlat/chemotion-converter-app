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

    for identifier in profile['identifiers']:
        identifier['key'] = identifier.pop('metadataKey', '')
        identifier['outputKey'] = identifier.pop('headerKey', '')
        identifier['outputLayer'] = ''
        identifier['outputTableIndex'] = ''

        if identifier['type'] == 'metadata':
            identifier['type'] = 'fileMetadata'
        elif identifier['type'] == 'table':
            identifier['type'] = 'tableHeader'

    output_file_path = output_path / input_file_path.name
    json.dump(profile, output_file_path.open('w'), indent=2)

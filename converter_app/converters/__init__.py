import json
import os

from .base import Converter

def match_profile(file_data_metadata):
    profiles_dir = os.getenv('PROFILES_DIR')
    profiles = os.listdir(profiles_dir)

    for file in profiles:
        file_path = os.path.join(profiles_dir, file)
        with open(file_path, 'r') as data_file:
            data_dict = json.load(data_file)
            converter = Converter(**data_dict)
            indentifiers = converter.identifiers
            if indentifiers.items() <= file_data_metadata.items():
                return converter

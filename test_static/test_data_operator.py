from pathlib import Path

from werkzeug.datastructures import FileStorage

from converters import Converter
from models import File, Profile
from readers import READERS


def test_is_operator_sample():
    profile_identifier = "c01ae8dc-b0fa-40c8-b894-7765f2b58c2e"
    profile_fp = Path(__file__).parent / "a" / f"{profile_identifier}.json"
    test_file_fp = Path(__file__).parent / "a" / "test_file.csv"
    with open(test_file_fp, 'r') as test_file:
        data = [float(x.split(';', 1)[0]) * 2 + 7 for x in test_file.readlines()[3:]]
    with open(test_file_fp, 'rb') as test_file:
        fs = FileStorage(stream=test_file, filename="test_file.csv",
                         content_type='text/csv')
        csv_reader = READERS.readers['ascii_reader'](File(fs))
        assert csv_reader.check()
        csv_reader.process()
        profile_data = Profile.load(profile_fp)
        profile = Profile(profile_data, 'dev', profile_identifier, False)
        converter = Converter(profile, csv_reader.as_dict)
        converter.process()
        assert [float(x) for x in converter.tables[0]['x']] == data

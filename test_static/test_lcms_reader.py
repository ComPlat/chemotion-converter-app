from pathlib import Path
from test_static.utils import HandleTestReader


def test_Tif7():
    test_file = Path(__file__).parent.parent / 'test_static/test_files/OpenLab.tar.gz'
    with HandleTestReader(test_file.__str__(), 'lcms_reader') as reader:
        assert len(reader.as_dict['tables']) == 2413
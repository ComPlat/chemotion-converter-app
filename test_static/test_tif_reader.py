from pathlib import Path
from test_static.utils import TestReader


def test_Tif7():
    test_file = Path(__file__).parent.parent / 'test_static/test_files/tif_Kleiner Hund A011.tif'
    with TestReader(test_file.__str__(), 'tif_reader') as reader:
        assert len(reader.as_dict['tables']) == 1

def test_Tif11():
    test_file = Path(__file__).parent.parent / 'test_static/test_files/tif_Kleiner.Hund.A007.tif'
    with TestReader(test_file.__str__(), 'tif_reader') as reader:
        assert len(reader.as_dict['tables']) == 1

def test_Tif17():
    test_file = Path(__file__).parent.parent / 'test_static/test_files/tiff_Diff_17.tif'
    with TestReader(test_file.__str__(), 'tif_reader') as reader:
        assert len(reader.as_dict['tables']) == 1
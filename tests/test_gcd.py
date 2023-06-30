import os

from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers import registry


def test_find_reader_cif_generic(app):
    gcd_file = "./tests/sample_files/EF-R94.3-40h__GC-BID_inc-5min-30_GC-3min-40-7min-180-2min_Calibrated_292023_904_003.gcd.txt"
    with open(gcd_file, 'rb') as f:
        fs = FileStorage(stream=f, filename=os.path.basename(gcd_file), content_type='chemical/x-cif')
        file = File(fs)
        reader = registry.match_reader(file, 'dev')
    assert reader.identifier == 'gcd_reader'

def test_processing(app):
    gcd_file = "./tests/sample_files/EF-R94.3-40h__GC-BID_inc-5min-30_GC-3min-40-7min-180-2min_Calibrated_292023_904_003.gcd.txt"
    with open(gcd_file, 'rb') as f:
        fs = FileStorage(stream=f, filename=os.path.basename(gcd_file), content_type='chemical/x-cif')
        file = File(fs)
        reader = registry.match_reader(file, 'dev')
    reader.process()
    tables = reader.tables
    assert len(tables) == 5
    assert tables[0]['metadata']['[Header].Application Name'] == 'LabSolutions'
    assert tables[1]['metadata']['Header'] == '[Compound Results(Ch1)]'
    assert tables[2]['metadata']['Header'] == '[Compound Results(Ch2)]'
    assert tables[3]['metadata']['Header'] == '[Chromatogram (Ch1)]'
    assert tables[4]['metadata']['Header'] == '[Chromatogram (Ch2)]'

    assert len(tables[3]['rows']) == 18001
    assert len(tables[3]['columns']) == 2
    assert len(tables[4]['rows']) == 18001
    assert len(tables[4]['columns']) == 2

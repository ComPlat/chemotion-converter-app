import os

from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers import registry


def test_find_reader_cif_generic(app):
    test_file = "./tests/sample_files/SG-V3545-6-13.cif"
    with open(test_file, 'rb') as f:
        fs = FileStorage(stream=f, filename=os.path.basename(test_file), content_type='chemical/x-cif')
        file = File(fs)
        reader = registry.match_reader(file)
    assert reader.identifier == 'cif_reader'

    test_file = "./tests/sample_files/zipped_cif.zip"
    with open(test_file, 'rb') as f:
        fs = FileStorage(stream=f, filename=os.path.basename(test_file), content_type='chemical/x-cif')
        file = File(fs)
        reader = registry.match_reader(file)
    assert reader.identifier == 'cif_reader'

    test_file = "./tests/sample_files/zipped_cfx_cif.zip"
    with open(test_file, 'rb') as f:
        fs = FileStorage(stream=f, filename=os.path.basename(test_file), content_type='chemical/x-cif')
        file = File(fs)
        reader = registry.match_reader(file)
    assert reader.identifier == 'cif_reader'

def test_find_reader_cfx_generic(app):
    test_file = "./tests/sample_files/SG-V3551-15-19.cfx_LANA"
    with open(test_file, 'rb') as f:
        fs = FileStorage(stream=f, filename=os.path.basename(test_file), content_type='chemical/x-cif')
        file = File(fs)
        reader = registry.match_reader(file)
    assert reader.identifier == 'cfx_reader'

    test_file = "./tests/sample_files/zipped_cfx.zip"
    with open(test_file, 'rb') as f:
        fs = FileStorage(stream=f, filename=os.path.basename(test_file), content_type='chemical/x-cif')
        file = File(fs)
        reader = registry.match_reader(file)
    assert reader.identifier == 'cfx_reader'

def test_processing(app):
    pass

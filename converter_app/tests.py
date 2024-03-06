import json
import os
import shutil
import traceback
import pytest
from werkzeug.datastructures import FileStorage

from converter_app.app import create_app
from converter_app.models import File
from converter_app.readers import READERS as registry

res_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ConverterAutoResults'))
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ChemConverter'))

@pytest.fixture
def app():
    """Get Flask app as fixture"""
    yield create_app


@pytest.fixture
def test_files():
    """Get Flask app as fixture"""
    yield {
        'res':res_path,
        'src':src_path
    }


def test_settings_list(app, client):
    """

    :param app: Flask app factory
    :param client: Flask client
    """

    app()
    response = client.get('/')
    assert response.status_code == 200


def test_all_reader(test_files):
    res_path = test_files['res']
    src_path = test_files['src']

    for ontology in os.listdir(src_path):
        ontology_path = os.path.join(src_path, ontology)
        if os.path.isdir(ontology_path):
            for device in os.listdir(ontology_path):
                device_path = os.path.join(src_path, ontology, device)
                if os.path.isdir(device_path):
                    for software in os.listdir(device_path):
                        software_path = os.path.join(src_path, ontology, device, software)
                        res_software_path = os.path.join(res_path, ontology, device, software)
                        for file in os.listdir(software_path):
                            print('Test:' + '/'.join([ontology, device, software , file]))
                            with open(os.path.join(software_path, file), 'rb') as fp:
                                file_storage = FileStorage(fp)
                                with open(os.path.join(res_software_path, file + '.json'), 'r') as f_res:
                                    expected_result = json.loads(f_res.read())
                                try:
                                    reader = registry.match_reader(File(file_storage))
                                    if reader:
                                        reader.process()
                                        content = reader.as_dict
                                        assert expected_result['tables'] == content['tables']
                                        assert expected_result['metadata']['extension'] == content['metadata']['extension']
                                        assert expected_result['metadata']['reader'] == content['metadata']['reader']
                                        assert expected_result['metadata']['mime_type'] == content['metadata']['mime_type']
                                    else:
                                        assert expected_result == {}
                                except:
                                    print(traceback.format_exc())
                                finally:
                                    f_res.close()
                                    file_storage.close()
                                pass

def prepare_tests():
    res_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ConverterAutoResults'))
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ChemConverter'))
    if os.path.isdir(res_path):
        shutil.rmtree(res_path)

    for ontology in os.listdir(src_path):
        ontology_path = os.path.join(src_path, ontology)
        if os.path.isdir(ontology_path):
            for device in os.listdir(ontology_path):
                device_path = os.path.join(src_path, ontology, device)
                if os.path.isdir(device_path):
                    for software in os.listdir(device_path):
                        software_path = os.path.join(src_path, ontology, device, software)
                        res_software_path = os.path.join(res_path, ontology, device, software)
                        os.makedirs(res_software_path)
                        for file in os.listdir(software_path):
                            print('/'.join([ontology, device, software , file]))
                            with open(os.path.join(software_path, file), 'rb') as fp:

                                file_storage = FileStorage(fp)



                                try:
                                    reader = registry.match_reader(File(file_storage))
                                    if reader:
                                        reader.process()
                                        content = json.dumps(reader.as_dict)
                                        with open(os.path.join(res_software_path, file + '.json'), 'w+') as f_res:
                                            f_res.write(content)
                                            f_res.close()
                                    else:
                                        raise Exception('No reader found')
                                except:
                                    print(traceback.format_exc())
                                    with open(os.path.join(res_software_path, file + '.json'), 'w+') as f_res:
                                        f_res.write('{}')
                                        f_res.close()
                                finally:
                                    file_storage.close()
                                pass
import json
import os
import shutil
import tempfile
import traceback
import zipfile

import flask

from werkzeug.datastructures import FileStorage

from converter_app.models import File

from converter_app.readers import READERS as registry
from test_manager.test_file_manager import PROFILE_PATH
from converter_app.converters import Converter
from converter_app.writers.jcampzip import JcampZipWriter

FLASK_APP = None

def compare_reader_result(src_path, res_path, file):
    with open(os.path.join(src_path, file), 'rb') as fp:
        file_storage = FileStorage(fp)
        with open(os.path.join(res_path, file + '.json'), 'r', encoding='utf8') as f_res:
            expected_result = json.loads(f_res.read())
            f_res.close()
            reader = registry.match_reader(File(file_storage))
            if reader:
                reader.process()
                content = reader.as_dict
                return (expected_result, content, True)
    return (expected_result, {}, False)


def get_profile_result(reader_dict, file):
    with set_flask_test_config().app_context():
        res_path = tempfile.mkdtemp()
        converter = Converter.match_profile('dev', reader_dict)
        try:
            if converter:
                converter.process()
                writer = JcampZipWriter(converter)
                writer.process()
                res_content = writer.write()
                with open(os.path.join(res_path, file + '.zip'), 'wb+') as f_res:
                    f_res.write(res_content)
                    f_res.close()
                with zipfile.ZipFile(str(os.path.join(res_path, file + '.zip'))) as zip_ref:
                    zip_ref.extractall(str(os.path.join(res_path, file)))
                data = []
                meta_data = []
                if os.path.exists(os.path.join(res_path, file, 'data')):
                    for data_file in os.listdir(os.path.join(res_path, file, 'data')):
                        with open(os.path.join(res_path, file, 'data', data_file), 'r', encoding='utf8') as f:
                            data.append(f.read())

                if os.path.exists(os.path.join(res_path, file, 'metadata')):
                    for data_file in os.listdir(os.path.join(res_path, file, 'metadata')):
                        with open(os.path.join(res_path, file, 'metadata', data_file), 'r', encoding='utf8') as f:
                            meta_data.append(json.loads(f.read()))
                return data, meta_data, True
            else:
                raise FileNotFoundError('No profile found')
        except FileNotFoundError:
            print('Reader or Profile not found')
            print(traceback.format_exc())
        except AssertionError:
            print('Profile not matching')
            print(traceback.format_exc())
        except AttributeError:
            print('Converter con not write')
            print(traceback.format_exc())
        finally:
            shutil.rmtree(res_path)
    return [], [], False


def compare_profile_result(src_path, res_path, file):
    expected = []
    is_values = []
    (expected_result, content, has_reader) = compare_reader_result(src_path, res_path, file)
    if has_reader:
        expected.append(expected_result['metadata']['reader'])
        is_values.append(content['metadata']['reader'])
        data, meta_data, has_profile = get_profile_result(content, file)
        is_values += meta_data + data
        data_expected = []
        meta_expected = []
        if os.path.exists(os.path.join(res_path, file, 'data')):
            for data_file in os.listdir(str(os.path.join(res_path, file, 'data'))):
                with open(os.path.join(res_path, file, 'data', data_file), 'r', encoding='utf8') as f:
                    data_expected.append(f.read())

        if os.path.exists(os.path.join(res_path, file, 'metadata')):
            for data_file in os.listdir(str(os.path.join(res_path, file, 'metadata'))):
                with open(os.path.join(res_path, file, 'metadata', data_file), 'r', encoding='utf8') as f:
                    meta_expected.append(json.loads(f.read()))
        expected += meta_expected + data_expected
    if len(is_values) > 1:
        pass
    return is_values, expected


def set_flask_test_config():
    global FLASK_APP
    if FLASK_APP is not None:
        return FLASK_APP
    FLASK_APP = flask.Flask(__name__, instance_relative_config=True)
    FLASK_APP.config.from_mapping(
        SECRET_KEY="123TEST",
        PROFILES_DIR=os.path.dirname(PROFILE_PATH),
        DATASETS_DIR='',
        MAX_CONTENT_LENGTH=64 * 1000 ** 2,
        CORS=True,
        DEBUG=True,
        CLIENTS=False
    )

    return FLASK_APP

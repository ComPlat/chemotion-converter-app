import json
import os
import flask

from werkzeug.datastructures import FileStorage

from converter_app.models import File

from converter_app.readers import READERS as registry
from test_manager.test_file_manager import PROFILE_PATH


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


def compare_profile_result(src_path, res_path, file):
    (expected_result, content, has_reader) = compare_reader_result(src_path, res_path, file)
    with open(os.path.join(res_path, file + '.json'), 'r', encoding='utf8') as f_res:
        expected_result = json.loads(f_res.read())
        if has_reader:
            reader = content['metadata']['reader']
            return expected_result, content, reader, has_reader

        return {}, content, None, has_reader


def set_flask_test_config():
    app = flask.Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="123TEST",
        PROFILES_DIR=PROFILE_PATH,
        DATASETS_DIR='',
        MAX_CONTENT_LENGTH=64 * 1000 ** 2,
        CORS=True,
        DEBUG=True,
        CLIENTS=False
    )

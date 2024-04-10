import json
import os
import re
import shutil
import traceback

from test_manager.test_file_manager import CURRENT_DIR, RES_PROFILE_PATH
from test_manager.utils import basic_walk
from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers import READERS as registry
from converter_app.converters import Converter

TEST_IDX = 0
TEST_FILE = os.path.abspath(os.path.join(CURRENT_DIR, './test_profiles.py'))


def _generate_profile_tests(src_path, file, _unused, res_path):
    """
    Generates Profile tests
    :param src_path:  path to test file directory
    :param file: name of the test file
    :param _unused: path to reader result file directory
    :param res_path: -> path to profile result file directory
    :return:
    """
    global TEST_IDX
    TEST_IDX += 1

    test_name = re.sub(r'[^A-Za-z0-9]', '_', file)
    with open(TEST_FILE, 'a', encoding='utf8') as test_file:
        test_file.write(f'\n\n\ndef test_{TEST_IDX}_{test_name}():'
                        f'\n    global all_reader'
                        f'\n    (b,a,c)=compare_profile_result(\'{src_path}\',\'{res_path}\',\'{file}\')'
                        f'\n    if not c:'
                        f'\n        assert a == {{}}'
                        f'\n        return')


def _generate_expected_profiles_results(src_path, file, _unused, res_path):
    """
    Generates list of expected Profile test files
    :param src_path:  path to test file directory
    :param file: name of the test file
    :param _unused: path to reader result file directory
    :param res_path: -> path to profile result file directory
    :return:
    """

    with open(os.path.join(src_path, file), 'rb') as file_pointer:
        file_storage = FileStorage(file_pointer)
        try:
            reader = registry.match_reader(File(file_storage))
            if reader:
                reader.process()
                reader_dict = reader.as_dict
                content = json.dumps(reader_dict)
                converter = Converter.match_profile('test', reader.as_dict)
                with open(os.path.join(res_path, file + '.json'), 'w+', encoding='utf8') as f_res:
                    f_res.write(content)
                    f_res.close()
            else:
                raise FileNotFoundError('No reader found')
        except FileNotFoundError:
            print(traceback.format_exc())
            with open(os.path.join(res_path, file + '.json'), 'w+', encoding='utf8') as f_res:
                f_res.write('{}')
                f_res.close()
        finally:
            file_storage.close()


def generate_expected_profiles_results():
    if os.path.isdir(RES_PROFILE_PATH):
        shutil.rmtree(RES_PROFILE_PATH)
    # basic_walk(_generate_expected_profiles_results)


def generate_profile_tests():
    global TEST_IDX

    TEST_IDX = 0
    with open(TEST_FILE, 'w+', encoding='utf8') as fp:
        fp.write("from .utils_test import compare_profile_result\n"
                 "from converter_app.readers import READERS as registry\n"
                 "\nall_reader = set()\n")
    basic_walk(_generate_profile_tests)
    with open(TEST_FILE, 'a', encoding='utf8') as fp:
        fp.write(f'\n\n\ndef test_all_reder():'
                 f'\n    assert sorted(all_reader) == sorted([x.__name__ for k,x in registry.readers.items()])')

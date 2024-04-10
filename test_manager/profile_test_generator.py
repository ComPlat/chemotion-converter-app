import json
import os
import re
import shutil
import traceback
import zipfile

from converter_app.writers.jcampzip import JcampZipWriter
from test_manager.test_file_manager import CURRENT_DIR, RES_PROFILE_PATH
from test_manager.utils import basic_walk
from werkzeug.datastructures import FileStorage

from converter_app.models import File
from converter_app.readers import READERS as registry
from converter_app.converters import Converter
from test_manager.utils_test import set_flask_test_config

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
                        f'\n    (a, b)=compare_profile_result(\'{src_path}\',\'{res_path}\',\'{file}\')'
                        f'\n    assert len(a) == len(b)'
                        f'\n    if len(a) > 0:'
                        f'\n        all_reader.add(a[0])'
                        f'\n    if len(a) > 1:'
                        f'\n        all_profiles.add(a[1].get("profileId"))'
                        f'\n    for idx, is_val in enumerate(a):'
                        f'\n        assert is_val == b[idx]')


def _generate_expected_profiles_results(src_path, file, _unused, res_path):
    """
    Generates list of expected Profile test files
    :param src_path:  path to test file directory
    :param file: name of the test file
    :param res_path: path to reader result file directory
    :param res_path: -> path to profile result file directory
    :return:
    """

    with open(os.path.join(src_path, file), 'rb') as file_pointer:
        file_storage = FileStorage(file_pointer)
        # os.makedirs(os.path.join(res_path, file) , exist_ok=True)
        reader_content_str = '{}'
        try:
            reader = registry.match_reader(File(file_storage))
            if reader:
                reader.process()
                reader_dict = reader.as_dict
                reader_content_str = json.dumps(reader_dict)
                converter = Converter.match_profile('dev', reader_dict)
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
                    with open(os.path.join(res_path, file + '.json'), 'w', encoding='utf8') as f_res:
                        f_res.write(reader_content_str)
                        f_res.close()
                else:
                    raise FileNotFoundError('No profile found')
            else:
                raise FileNotFoundError('No reader found')
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
            with open(os.path.join(res_path, file + '.json'), 'w+', encoding='utf8') as f_res:
                f_res.write(reader_content_str)
                f_res.close()
            file_storage.close()


def generate_expected_profiles_results():
    app = set_flask_test_config()
    with app.app_context():
        if os.path.isdir(RES_PROFILE_PATH):
            shutil.rmtree(RES_PROFILE_PATH)
        basic_walk(_generate_expected_profiles_results)


def generate_profile_tests():
    global TEST_IDX

    TEST_IDX = 0
    with open(TEST_FILE, 'w+', encoding='utf8') as fp:
        fp.write("from .utils_test import compare_profile_result\n"
                 "from converter_app.readers import READERS as registry\n"
                 "from converter_app.models import Profile\n"
                 "\nall_reader = set()"
                 "\nall_profiles = set()\n")
    basic_walk(_generate_profile_tests)
    with open(TEST_FILE, 'a', encoding='utf8') as fp:
        fp.write(f'\n\n\ndef test_all_reader():'
                 f'\n    assert sorted(all_reader) == sorted([x.__name__ for k,x in registry.readers.items()])'
                 f'\n\n\ndef test_all_profiles():'
                 f'\n    assert sorted(all_profiles) == sorted([x.id for x in Profile.list("dev")])')

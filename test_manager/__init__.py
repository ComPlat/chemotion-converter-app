import argparse
import importlib
import json
import os
import re
import sys
import traceback
from json import JSONDecodeError

from werkzeug.datastructures import FileStorage


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_manager.profile_test_generator import generate_profile_tests, generate_expected_profiles_results
from test_manager.utils import basic_walk
from test_manager.test_file_manager import PROFILE_PATH, PARENT_DIR, CURRENT_DIR, load_profiles_from_git, \
    RES_READER_PATH

TEST_FILE = os.path.abspath(os.path.join(CURRENT_DIR, './test_readers.py'))
TEST_IDX = 0
TEST_DICT = {}

from converter_app.models import File
from converter_app.readers import READERS as registry


def generate_expected_results(src_path, file, res_path, _unused):
    src_path_file = os.path.join(src_path, file)
    final_targe_file = os.path.join(res_path, file + '.json')
    if os.path.exists(final_targe_file) and src_path_file in TEST_DICT:
        try:
            mod = importlib.import_module('test_manager.test_readers')
            getattr(mod, TEST_DICT[src_path_file])()
            return
        except (ModuleNotFoundError, FileNotFoundError, AssertionError, JSONDecodeError):
            pass
    print(f"Generating expected results for {src_path_file}")
    with open(src_path_file, 'rb') as file_pointer:
        file_storage = FileStorage(file_pointer)
        try:
            reader = registry.match_reader(File(file_storage))
            if reader:
                reader.process()
                content = json.dumps(reader.as_dict)
                with open(final_targe_file, 'w+', encoding='utf8') as f_res:
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


def generate_test(src_path, file, res_path, _unused):
    global TEST_IDX
    TEST_IDX += 1

    test_name = re.sub(r'[^A-Za-z0-9]', '_', file)
    test_name = f'test_{TEST_IDX}_{test_name}'
    TEST_DICT[os.path.join(src_path, file)] = test_name
    with open(TEST_FILE, 'a', encoding='utf8') as test_file:

        test_file.write(f'\n\n\ndef {test_name}():'
                        f'\n    global all_reader'
                        f'\n    (b,a,c)=compare_reader_result(r\'{src_path}\',r\'{res_path}\',r\'{file}\')'
                        f'\n    if not c:'
                        f'\n        assert a == {{}}'
                        f'\n        return'
                        f'\n    all_reader.add(a[\'metadata\'][\'reader\'])'
                        f'\n    compare_tables(a[\'tables\'], b[\'tables\'])'
                        f'\n    assert a[\'metadata\'][\'extension\'] == b[\'metadata\'][\'extension\']'
                        f'\n    assert a[\'metadata\'][\'reader\'] == b[\'metadata\'][\'reader\']'
                        f'\n    assert a[\'metadata\'][\'mime_type\'] == b[\'metadata\'][\'mime_type\']')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='ChemConverter Test Manager',
        description='Generates test script for all reader and expected result')
    # positional argument
    parser.add_argument('-e', '--expected', action='store_true')
    parser.add_argument('-ep', '--expected_profiles', action='store_true')
    parser.add_argument('-t', '--tests', action='store_true')
    parser.add_argument('-tp', '--test_profiles', action='store_true')
    parser.add_argument('-g', '--github', action='store_true')
    args = parser.parse_args()
    if args.github:
        load_profiles_from_git()
    if args.tests or args.expected:
        TEST_IDX = 0
        TEST_DICT = {}
        with open(TEST_FILE, 'w+', encoding='utf8') as fp:
            fp.write("import pytest\n"
                     "from .utils_test import compare_reader_result, compare_tables\n"
                     "from converter_app.readers import READERS as registry\n"
                     "\nall_reader = set()\n")
        basic_walk(generate_test)
        with open(TEST_FILE, 'a') as fp:
            fp.write(f'\n\n\n# Uncomment to check if all reader are tested.'
                     f'\n# def test_all_reader():'
                     f'\n#    assert sorted(all_reader) == sorted([x.__name__ for k,x in registry.readers.items()])')
    if args.expected:
        basic_walk(generate_expected_results)
    if args.test_profiles or args.expected_profiles:
        generate_profile_tests()
    if args.expected_profiles:
        generate_expected_profiles_results()

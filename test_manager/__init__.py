import argparse
import json
import os
import re
import shutil
import sys
import traceback

from werkzeug.datastructures import FileStorage

from converter_app.models import File

from converter_app.readers import READERS as registry

# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory by going one level up
parent_dir = os.path.dirname(current_dir)
# Add the parent directory to sys.path
sys.path.append(parent_dir)

global_res_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ConverterAutoResults'))
global_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ChemConverter'))
global_test_file = os.path.abspath('./test_readers.py')

global_test_idx = 0

def generate_expected_results(src_path, res_path, file):
    with open(os.path.join(src_path, file), 'rb') as fp:
        file_storage = FileStorage(fp)
        try:
            reader = registry.match_reader(File(file_storage))
            if reader:
                reader.process()
                content = json.dumps(reader.as_dict)
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

def generate_test(src_path, res_path, file):
    global global_test_idx
    global_test_idx += 1

    test_name = re.sub(r'[^A-Za-z0-9]', '_', file)
    with open(global_test_file, 'a') as fp:
        fp.write(f'\n\n\ndef test_{global_test_idx}_{test_name}():'
                 f'\n    global all_reader'
                 f'\n    (b,a,c)=compare_reader_result(\'{src_path}\',\'{res_path}\',\'{file}\')'
                 f'\n    if not c:'
                 f'\n        assert a == {{}}'
                 f'\n        return'
                 f'\n    all_reader.add(a[\'metadata\'][\'reader\'])'
                 f'\n    assert a[\'tables\'] == b[\'tables\']'
                 f'\n    assert a[\'metadata\'][\'extension\'] == b[\'metadata\'][\'extension\']'
                 f'\n    assert a[\'metadata\'][\'reader\'] == b[\'metadata\'][\'reader\']'
                 f'\n    assert a[\'metadata\'][\'mime_type\'] == b[\'metadata\'][\'mime_type\']')




def basic_walk(callback):

    for ontology in os.listdir(global_src_path):
        ontology_path = os.path.join(global_src_path, ontology)
        if os.path.isdir(ontology_path):
            for device in os.listdir(ontology_path):
                device_path = os.path.join(global_src_path, ontology, device)
                if os.path.isdir(device_path):
                    for software in os.listdir(device_path):
                        software_path = os.path.join(global_src_path, ontology, device, software)
                        res_software_path = os.path.join(global_res_path, ontology, device, software)
                        os.makedirs(res_software_path, exist_ok=True)
                        for file in os.listdir(software_path):
                            print('/'.join([ontology, device, software, file]))
                            callback(software_path, res_software_path, file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='ChemConverter Test Manager',
        description='Generates test script for all reader and expected result')
    # positional argument
    parser.add_argument('-e', '--expected', action='store_true')
    parser.add_argument('-t', '--tests', action='store_true')
    args = parser.parse_args()
    if args.expected:
        if os.path.isdir(global_res_path):
            shutil.rmtree(global_res_path)
        basic_walk(generate_expected_results)
    if args.tests:
        global_test_idx = 0
        with open(global_test_file, 'w+') as fp:
            fp.write("from .utils_test import compare_reader_result\n"
                     "from converter_app.readers import READERS as registry\n"
                     "\nall_reader = set()\n")
        basic_walk(generate_test)
        with open(global_test_file, 'a') as fp:
            fp.write(f'\n\n\ndef test_all_reder():'
                     f'\n    assert sorted(all_reader) == sorted([x.__name__ for k,x in registry.readers.items()])')

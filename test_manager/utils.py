import os

from test_manager.test_file_manager import DATA_FILE_PATH, RES_PROFILE_PATH, RES_READER_PATH


def _walk_step(src_path: str):
    for entry in os.listdir(src_path):
        entry_path = os.path.join(src_path, entry)
        if os.path.isdir(entry_path):
            yield entry, entry_path


def basic_walk(callback):
    """
    Walks over all test files and calls the callback function with four arguments:
    1 -> path to test file directory
    2 -> name of the test file
    3 -> path to reader result file directory
    4 -> path to profile result file directory
    :param callback: callable handler, needs to accept four string arguments
    :return:
    """
    for ontology, ontology_path in _walk_step(DATA_FILE_PATH):
        for device, device_path in _walk_step(ontology_path):
            for software, software_path in _walk_step(device_path):
                res_profile_path = os.path.join(RES_PROFILE_PATH, ontology, device, software)
                res_reader_path = os.path.join(RES_READER_PATH, ontology, device, software)
                os.makedirs(res_profile_path, exist_ok=True)
                os.makedirs(res_reader_path, exist_ok=True)
                for file in os.listdir(software_path):
                    print('/'.join([ontology, device, software, file]))
                    callback(software_path, file, res_reader_path, res_profile_path)

import os
import shutil

from converter_app.utils import load_public_profiles

# Get the current script's directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory by going one level up
PARENT_DIR = os.path.dirname(CURRENT_DIR)
# Profile directory
PROFILE_PATH = os.path.abspath(os.path.join(PARENT_DIR, 'test_files/profiles/dev'))
DATA_FILE_PATH = os.path.abspath(os.path.join(PARENT_DIR, 'test_files/data_files'))
# Path to profile result file directory
RES_PROFILE_PATH = os.path.abspath(os.path.join(CURRENT_DIR, 'profile_results'))
# Path to reader result file directory
RES_READER_PATH = os.path.abspath(os.path.join(CURRENT_DIR, 'reader_results'))


def load_profiles_from_git(only_test_files=False):
    """
    Load profiles from git repository.
    :return:
    """
    # Copy desired file from temporary dir
    profile_path = None
    if not only_test_files and os.path.isdir(PROFILE_PATH):
        profile_path = PROFILE_PATH
        shutil.rmtree(profile_path)
    if os.path.isdir(DATA_FILE_PATH):
        shutil.rmtree(DATA_FILE_PATH)
    load_public_profiles(profile_path, DATA_FILE_PATH)

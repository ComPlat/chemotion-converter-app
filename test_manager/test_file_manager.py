import os
import shutil
import tempfile
import git

# Get the current script's directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the parent directory by going one level up
PARENT_DIR = os.path.dirname(CURRENT_DIR)
# Profile directory
PROFILE_PATH = os.path.abspath(os.path.join(PARENT_DIR, 'test_files/profiles'))
DATA_FILE_PATH = os.path.abspath(os.path.join(PARENT_DIR, 'test_files/data_files'))
# Path to profile result file directory
RES_PROFILE_PATH = os.path.abspath(os.path.join(PARENT_DIR, 'test_files/profile_results'))
# Path to reader result file directory
RES_READER_PATH = os.path.abspath(os.path.join(PARENT_DIR, 'test_files/reader_results'))


def load_profiles_from_git():
    t = tempfile.mkdtemp()
    # Clone into temporary dir
    git.Repo.clone_from('https://github.com/ComPlat/chemotion_saurus.git', t, branch='added_data_files', depth=1)
    # Copy desired file from temporary dir
    if os.path.isdir(PROFILE_PATH):
        shutil.rmtree(PROFILE_PATH)
    if os.path.isdir(DATA_FILE_PATH):
        shutil.rmtree(DATA_FILE_PATH)
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
    shutil.move(os.path.join(t, 'static/files/shared_ChemConverter_files/profiles'), PROFILE_PATH)
    shutil.move(os.path.join(t, 'static/files/shared_ChemConverter_files/data_files'), DATA_FILE_PATH)
    # Remove temporary dir
    shutil.rmtree(t)

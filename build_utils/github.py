import os
import shutil
import tempfile
from pathlib import Path

import git

def reset_folder(path: Path) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

def move_contents(src: Path, dst: Path) -> None:
    reset_folder(dst)

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        shutil.move(s, d)

def load_client_build(dest: Path, repo = 'ComPlat/chemotion-converter-client', branch: str = 'master'):


    with tempfile.TemporaryDirectory() as t:
        # Clone into temporary dir
        git.Repo.clone_from(f'https://github.com/{repo}', t, branch=branch, depth=1)

        move_contents(Path(t) / 'build', dest)
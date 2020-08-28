import json
from pathlib import Path

from flask import current_app as app


def write_tmp_file(uuid, data):
    tmp_path = Path(app.config['TMP_DIR'])
    tmp_path.mkdir(parents=True, exist_ok=True)
    file_name = Path(uuid).with_suffix('.json')
    with open(tmp_path / file_name, 'w') as f:
        json.dump(data, f)


def read_tmp_file(uuid):
    tmp_path = Path(app.config['TMP_DIR'])
    file_name = Path(uuid).with_suffix('.json')
    with open(tmp_path / file_name) as f:
        return json.load(f)


def delete_tmp_file(uuid):
    tmp_path = Path(app.config['TMP_DIR'])
    file_name = Path(uuid).with_suffix('.json')
    tmp_path.joinpath(file_name).unlink()

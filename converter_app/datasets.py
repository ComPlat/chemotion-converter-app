import json
import logging
import uuid
from collections import defaultdict
from pathlib import Path

from flask import current_app

from .utils import check_uuid

logger = logging.getLogger(__name__)


class Dataset(object):

    def __init__(self, dataset_data, ols=None):
        self.dataset_data = dataset_data
        self.ols = ols

    @classmethod
    def list(cls):
        datasets_path = Path(current_app.config['DATASETS_DIR'])

        if datasets_path.exists():
            for file_path in Path.iterdir(datasets_path):
                dataset_data = json.loads(file_path.read_text())
                yield cls(dataset_data, dataset_data['ols'])
        else:
            return []

    @classmethod
    def retrieve(cls, type):
        datasets_path = Path(current_app.config['DATASETS_DIR'])

        return False
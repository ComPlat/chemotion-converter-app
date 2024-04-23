import json
import logging
from pathlib import Path

from flask import current_app

logger = logging.getLogger(__name__)


class Dataset:
    """
    Dataset manager object. Make sure that the DATASETS_DIR env variable must be set.
    Properties
        dataset_data, ols
    """

    def __init__(self, dataset_data, ols=None):
        self.dataset_data = dataset_data
        self.ols = ols

    @classmethod
    def list(cls) -> list:
        """
        Lists all datasets.

        :return: List of all datasets
        """
        datasets_path = Path(current_app.config['DATASETS_DIR'])

        if datasets_path.exists():
            for file_path in Path.iterdir(datasets_path):
                dataset_data = json.loads(file_path.read_text())
                yield cls(dataset_data, dataset_data['ols'])
        return []

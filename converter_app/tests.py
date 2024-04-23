import json
import os
import shutil
import traceback
import pytest
from werkzeug.datastructures import FileStorage

from converter_app.app import create_app
from converter_app.models import File
from converter_app.readers import READERS as registry

res_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ConverterAutoResults'))
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ChemConverter'))

@pytest.fixture
def app():
    """Get Flask app as fixture"""
    yield create_app


@pytest.fixture
def test_files():
    """Get Flask app as fixture"""
    yield {
        'res':res_path,
        'src':src_path
    }


def test_settings_list(app, client):
    """

    :param app: Flask app factory
    :param client: Flask client
    """

    app()
    response = client.get('/')
    assert response.status_code == 200
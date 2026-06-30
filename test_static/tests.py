import os
import tempfile

import pytest
from flask import Flask
from flask.testing import FlaskClient
from werkzeug.datastructures import FileStorage

from converter_app.app import create_app
from converter_app.models import File, extract_tar_archive

res_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ConverterAutoResults'))
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../test_files/ChemConverter'))


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    # create the app with common test config
    yield create_app()

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app: Flask):
    """
    A test client for the app.
    """

    return app.test_client()


@pytest.fixture
def test_files():
    """Get Flask app as fixture"""
    yield {
        'res': res_path,
        'src': src_path
    }


def test_settings_list(client: FlaskClient):
    """
    Test setting tests
    :param client: Flask client
    """

    response = client.get('/')
    assert response.status_code == 200



def test_tar_unzip(client: FlaskClient):
    """
    Test setting tests
    :param client: Flask client
    """

    with open(os.path.join(os.path.dirname(__file__), 'a/a.tar.gz'), 'rb') as tar:
        fs = FileStorage(stream=tar, filename='a/a.tar.gz',
                         content_type='application/tar')
        file = File(fs)
        assert file.is_tar_archive
        assert file.name == 'a.tar.gz'
        with open(os.path.join(os.path.dirname(__file__), 'a/a.txt.0'), 'r') as tf:
            archive = extract_tar_archive(file)
            assert len(archive) == 1
            assert archive[0].name == 'a.txt.0'
            assert archive[0].string == tf.read()

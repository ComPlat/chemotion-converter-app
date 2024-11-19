import os
import tempfile

import pytest
from flask import Flask
from flask.testing import FlaskClient

from converter_app.app import create_app

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

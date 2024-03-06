import pytest

from converter_app.app import create_app


@pytest.fixture
def app():
    """Get Flask app as fixture"""
    yield create_app


def test_settings_list(app, client):
    """

    :param app: Flask app factory
    :param client: Flask client
    """

    app()
    response = client.get('/')
    assert response.status_code == 200

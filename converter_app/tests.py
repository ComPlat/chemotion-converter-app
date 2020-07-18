import pytest

from . import create_app


@pytest.fixture
def app():
    return create_app()


def test_settings_list(app, client):
    response = client.get('/')
    assert response.status_code == 200

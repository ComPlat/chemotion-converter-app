import pytest
import json
from converter_app.app import create_app

@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        'PROFILES_DIR': 'tests/profiles',
        'READERS_DIR': 'tests/readers',
    })

    # other setup can go here

    yield app

    # clean up / reset resources here


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

@pytest.fixture()
def reader_params():
    client_id = 'dev'
    reader_id = 'dce9aee4-8c59-46f3-9391-bdccee3f5ce6'

    with open('./tests/readers/dev/dce9aee4-8c59-46f3-9391-bdccee3f5ce6.json', 'r') as f:
        data = json.loads(f.read())

    return {
       'client_id': client_id,
       'reader_data': data,
       'reader_id': reader_id,
    }

@pytest.fixture()
def test_reader(reader_params):
    return Reader(**reader_params)
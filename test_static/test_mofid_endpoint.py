import io
import os
import shutil

import pytest
from flask import Flask
from flask.testing import FlaskClient

from converter_app.app import create_app
from converter_app.readers import cif as cif_module

CIF_DIR = os.path.join(os.path.dirname(__file__), 'test_files', 'cif_files')

MOFID_KEYS = {
    'mofid.mofid', 'mofid.mofkey', 'mofid.smiles', 'mofid.smiles_nodes',
    'mofid.smiles_linkers', 'mofid.topology', 'mofid.cat',
    'mofid.ccdc_number', 'mofid.node_ratios', 'mofid.linker_ratios',
}

# The mofid pipeline needs the Linux x86_64 wheel and Java (Systre) for the topology.
requires_mofid = pytest.mark.skipif(
    cif_module.cif2mofid is None or shutil.which('java') is None,
    reason='mofid_wrapper or a Java runtime is not available')


@pytest.fixture
def app():
    yield create_app()


@pytest.fixture
def client(app: Flask):
    return app.test_client()


def _post_cif(client: FlaskClient, file_name: str):
    with open(os.path.join(CIF_DIR, file_name), 'rb') as cif_file:
        return client.post('/mofid', data={'file': (cif_file, file_name)},
                           content_type='multipart/form-data')


@requires_mofid
@pytest.mark.timeout(300)
@pytest.mark.parametrize('file_name, expected', [
    ('P1-Cu-BTC.cif', {
        'mofid.smiles_nodes': '[Cu][Cu]',
        'mofid.smiles_linkers': '[O-]C(=O)c1cc(cc(c1)C(=O)[O-])C(=O)[O-]',
        'mofid.topology': 'tbo',
        'mofid.cat': '0',
        'mofid.ccdc_number': '',
        # Cu3(BTC)2: 24 paddlewheels and 32 linkers in the cell
        'mofid.node_ratios': '3',
        'mofid.linker_ratios': '4',
    }),
    ('P1-IRMOF-1.cif', {
        'mofid.smiles_nodes': '[Zn][O]([Zn])([Zn])[Zn]',
        'mofid.smiles_linkers': '[O-]C(=O)c1ccc(cc1)C(=O)[O-]',
        'mofid.topology': 'pcu',
        'mofid.cat': '0',
        'mofid.ccdc_number': '',
        # The unit cell cuts Zn4O clusters, so no trustworthy ratio is reported
        'mofid.node_ratios': '',
        'mofid.linker_ratios': '',
    }),
])
def test_mofid(client: FlaskClient, file_name, expected):
    response = _post_cif(client, file_name)

    assert response.status_code == 200
    result = response.get_json()
    assert set(result) == MOFID_KEYS
    for key, value in expected.items():
        assert result[key] == value, key

    name = os.path.splitext(file_name)[0]
    topology = expected['mofid.topology']
    assert result['mofid.smiles'] in (
        f"{expected['mofid.smiles_nodes']}.{expected['mofid.smiles_linkers']}",
        f"{expected['mofid.smiles_linkers']}.{expected['mofid.smiles_nodes']}")
    assert result['mofid.mofid'].startswith(f"{result['mofid.smiles']} MOFid-v1.{topology}.cat0")
    assert result['mofid.mofid'].endswith(f';{name}')
    assert f'.MOFkey-v1.{topology}' in result['mofid.mofkey']


def test_mofid_without_file(client: FlaskClient):
    response = client.post('/mofid', data={}, content_type='multipart/form-data')

    assert response.status_code == 400
    assert response.get_json() == {'error': 'File could not be used to generate MOFid'}


def test_mofid_with_non_cif_file(client: FlaskClient):
    response = client.post('/mofid', data={'file': (io.BytesIO(b'no cif here'), 'test.txt')},
                           content_type='multipart/form-data')

    assert response.status_code == 400
    assert response.get_json() == {'error': 'File could not be used to generate MOFid'}

"""Minimal HTTP wrapper around the snurr-group `mofid` pipeline.

Tier 1 of the converter's MOF support: POST a CIF, get the seven MOFid
identifiers back. Kept deliberately API-compatible with the Chemotion ELN's
mof_service, so MOFID_SERVICE_URL can point at either one -- this service just
returns fewer keys (no CCDC number, no component ratios), which is why it does
not need the OpenBabel Python bindings and stays a much smaller image.
"""

import logging
import os
import re
import shutil
import tempfile

from flask import Flask, jsonify, request

from mofid.run_mofid import cif2mofid

logger = logging.getLogger('mofid_service')
logger.setLevel(logging.INFO)
_gunicorn_logger = logging.getLogger('gunicorn.error')
if _gunicorn_logger.handlers:
    logger.handlers = _gunicorn_logger.handlers
else:
    logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB; CIFs are small

RESULT_KEYS = (
    'mofid',
    'mofkey',
    'smiles',
    'smiles_nodes',
    'smiles_linkers',
    'topology',
    'cat',
)

_UNSAFE_NAME_CHARS = re.compile(r'[^A-Za-z0-9._-]')


def _safe_cif_name(name):
    """The file name becomes the ';<name>' suffix of the MOFid, so sanitise it."""
    stem = os.path.splitext(os.path.basename(name or ''))[0]
    stem = _UNSAFE_NAME_CHARS.sub('_', stem).strip('_')
    return f'{stem or "structure"}.cif'


def _extract_cif():
    """Read CIF text from a JSON body, a multipart file, or the raw body."""
    if request.is_json:
        payload = request.get_json(silent=True)
        # A valid JSON body is authoritative; only fall through when parsing failed.
        if payload is not None:
            return payload.get('cif') or None, payload.get('name')
    if 'file' in request.files:
        handle = request.files['file']
        return handle.read().decode('utf-8', 'replace'), handle.filename
    if request.data:
        return request.data.decode('utf-8', 'replace'), None
    return None, None


@app.route('/health', methods=['GET'])
def health():
    """Liveness probe, used by the container health check and install docs."""
    return jsonify(status='ok')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Return the seven MOFid identifiers for the posted CIF."""
    cif_text, name = _extract_cif()
    if not cif_text or not cif_text.strip():
        return jsonify(error='No CIF provided'), 400
    logger.info('analyze: received CIF (%d bytes, name=%s)', len(cif_text), name)

    workdir = tempfile.mkdtemp(prefix='mofid_')
    try:
        cif_path = os.path.join(workdir, _safe_cif_name(name))
        with open(cif_path, 'w', encoding='utf-8') as handle:
            handle.write(cif_text)

        # cwd is /opt/app, which holds no .git, so the commit_ref baked into the
        # MOFid/MOFkey stays NO_REF and results are reproducible across hosts.
        result = cif2mofid(cif_path, output_path=os.path.join(workdir, 'Output'))
        return jsonify({key: result.get(key) for key in RESULT_KEYS})
    except Exception as error:  # pylint: disable=broad-exception-caught
        # Surface any pipeline failure to the caller rather than a 500 traceback.
        logger.warning('analyze failed: %s', error)
        return jsonify(error=str(error)), 500
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006)

"""Resolve MOFid/MOFkey metadata for a CIF file.

Three tiers are tried in this order (see helper/mofid/README.md):

  1. service  MOFID_SERVICE_URL points at a running mofid service -- either the
              ELN's own mof_service or the image built from helper/mofid/Dockerfile
              (port 5006).
  2. native   MOFID_HOME points at a local mofid build (helper/mofid/install_mofid.sh),
              or the `mofid` package is importable in the current interpreter.
  3. off      neither is configured; no MOF metadata is added and the CIF reader
              behaves exactly as before. This is the default.

Tier 2 runs the pipeline in a subprocess instead of importing it. mofid sets
BABEL_DATADIR as an import side effect, and it derives the commit_ref that ends
up inside the MOFid/MOFkey from `.git/ORIG_HEAD` *relative to the current working
directory* -- run in-process from a git checkout, the converter's own commit hash
would be baked into every identifier. A subprocess with a pinned cwd keeps both
out of the worker and allows a hard timeout.
"""

import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from importlib.util import find_spec
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# The identifiers we surface, as returned by mofid.run_mofid.cif2mofid.
RESULT_KEYS = (
    'mofid',
    'mofkey',
    'smiles',
    'smiles_nodes',
    'smiles_linkers',
    'topology',
    'cat',
)

METADATA_PREFIX = 'mofid.'

DEFAULT_TIMEOUT = 180

# Kept short and separate from the read timeout: a service that is configured but
# not running must not stall every CIF conversion for the full read timeout.
CONNECT_TIMEOUT = 5

# A broken native install fails *silently*: sbu cannot start, mofid swallows the
# non-zero exit code and reports the same '*'/'NA'/'no_mof' result that a genuine
# non-MOF CIF produces. These stderr markers tell the two apart, so a misinstalled
# pipeline drops its metadata instead of claiming the structure is not a MOF.
_BROKEN_INSTALL_MARKERS = (
    'error while loading shared libraries',
    'Unable to find OpenBabel plugins',
    'cannot write output format',
)

_UNSAFE_NAME_CHARS = re.compile(r'[^A-Za-z0-9._-]')

_FALSE_VALUES = ('0', 'false', 'no', 'off')


def _timeout():
    try:
        return max(1, int(os.getenv('MOFID_TIMEOUT') or DEFAULT_TIMEOUT))
    except ValueError:
        return DEFAULT_TIMEOUT


def _mofid_importable():
    try:
        spec = find_spec('mofid')
    except (ImportError, ValueError):
        return False
    # Any bare directory called 'mofid' on sys.path -- a checkout next to the
    # working directory, for instance -- registers as a namespace package with no
    # origin. Only a real installation has an __init__ module behind it.
    return spec is not None and spec.origin is not None


def resolve_tier():
    """Return (tier, target): ('service', url), ('native', home_or_None) or (None, None)."""
    if os.getenv('MOFID_ENABLED', 'true').strip().lower() in _FALSE_VALUES:
        return None, None

    url = (os.getenv('MOFID_SERVICE_URL') or '').strip()
    if url:
        return 'service', url

    home = (os.getenv('MOFID_HOME') or '').strip()
    if home:
        return 'native', home

    if _mofid_importable():
        return 'native', None

    return None, None


def _safe_cif_name(name):
    """A file name mofid can work with -- it becomes the ';<name>' part of the MOFid."""
    stem = Path(name or '').stem
    stem = _UNSAFE_NAME_CHARS.sub('_', stem).strip('_')
    return f'{stem or "structure"}.cif'


def _native_env(home):
    """Environment for the subprocess, with mofid on PYTHONPATH when needed."""
    env = dict(os.environ)
    search_paths = []

    explicit = (os.getenv('MOFID_PYTHONPATH') or '').strip()
    if explicit:
        search_paths.append(explicit)
    elif home:
        # install_mofid.sh creates <home>/pythonpath/mofid -> <home>/Python, because
        # the package directory in the mofid checkout is called 'Python', not 'mofid'.
        link_dir = Path(home) / 'pythonpath'
        if (link_dir / 'mofid').exists():
            search_paths.append(str(link_dir))

    if search_paths:
        inherited = env.get('PYTHONPATH')
        if inherited:
            search_paths.append(inherited)
        env['PYTHONPATH'] = os.pathsep.join(search_paths)

    return env


def _parse_json_payload(stdout):
    """run_mofid prints the JSON dict last; the C++ helpers chatter before it."""
    for line in reversed((stdout or '').strip().splitlines()):
        line = line.strip()
        if line.startswith('{'):
            return json.loads(line)
    raise RuntimeError('no JSON payload in mofid output')


def _from_native(cif_text, name, home, timeout):
    with tempfile.TemporaryDirectory(prefix='mofid_') as workdir:
        cif_path = Path(workdir) / _safe_cif_name(name)
        cif_path.write_text(cif_text, encoding='utf-8')

        process = subprocess.run(
            [sys.executable, '-m', 'mofid.run_mofid',
             str(cif_path), str(Path(workdir) / 'Output'), 'json'],
            cwd=workdir, env=_native_env(home), capture_output=True, text=True,
            timeout=timeout, check=False)

        stderr = process.stderr or ''
        broken = next((marker for marker in _BROKEN_INSTALL_MARKERS if marker in stderr), None)
        if broken is not None:
            raise RuntimeError(f'mofid installation is not usable: {broken}')
        if process.returncode != 0:
            raise RuntimeError((stderr.strip() or f'exit code {process.returncode}')[-300:])

        return _parse_json_payload(process.stdout)


def _from_service(url, cif_text, name, timeout):
    response = requests.post(f'{url.rstrip("/")}/analyze',
                             json={'cif': cif_text, 'name': name},
                             timeout=(CONNECT_TIMEOUT, timeout))
    response.raise_for_status()
    payload = response.json()
    if payload.get('error'):
        raise RuntimeError(str(payload['error'])[:300])
    return payload


def _as_metadata(result):
    """Flatten the mofid result into 'mofid.<key>' string metadata."""
    metadata = {}
    for key in RESULT_KEYS:
        value = result.get(key)
        if isinstance(value, (list, tuple)):
            value = '.'.join(str(item) for item in value if item not in (None, ''))
        metadata[f'{METADATA_PREFIX}{key}'] = '' if value is None else str(value)

    if not any(metadata.values()):
        raise RuntimeError('mofid returned an empty result')

    return metadata


def mofid_metadata(cif_text, name=None):
    """Return {'mofid.<key>': str} for a CIF, or None when unavailable.

    Never raises: MOF identification is an optional enrichment, so any failure is
    logged and the CIF conversion continues without it.
    """
    tier, target = resolve_tier()
    if tier is None:
        return None

    if not (cif_text or '').strip():
        logger.debug('mofid: no CIF content to analyse')
        return None

    timeout = _timeout()
    try:
        if tier == 'service':
            result = _from_service(target, cif_text, name, timeout)
        else:
            result = _from_native(cif_text, name, target, timeout)
        return _as_metadata(result)
    except subprocess.TimeoutExpired:
        logger.warning('mofid: %s tier timed out after %ds', tier, timeout)
    except requests.RequestException as error:
        logger.warning('mofid: service at %s unreachable: %s', target, error)
    except Exception as error:  # pylint: disable=broad-exception-caught
        # Enrichment must never break the conversion of an otherwise valid CIF.
        logger.warning('mofid: %s tier failed: %s', tier, error)
    return None


def add_mofid_metadata(table, cif_text, name=None):
    """Add the 'mofid.<key>' entries to a table. Returns True when they were added."""
    metadata = mofid_metadata(cif_text, name)
    if not metadata:
        return False
    for key, value in metadata.items():
        table.add_metadata(key, value)
    return True

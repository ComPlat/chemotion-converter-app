# -*- mode: python ; coding: utf-8 -*-
# --- standard imports ---
import sys, os
sys.path.append(os.path.abspath("./build_utils"))
from pathlib import Path
from github import load_client_build

# --- custom pre-build step ---
EXTERNAL_DIR = Path("client_build")

load_client_build(EXTERNAL_DIR, branch='ontologie_selector')

# --- normal PyInstaller stuff ---
block_cipher = None

a = Analysis(
    ['converter_app/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[('converter_app/', 'converter_app/'), ('client_build/', 'client_build/')],
    hiddenimports=['numpy', 'yadg', 'yadg.extractors.eclab.techniques', 'fitz', 'openpyxl', 'gemmi', 'jcamp', 'opusFC', 'xmltodict', 'hplc'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ChemConverterApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

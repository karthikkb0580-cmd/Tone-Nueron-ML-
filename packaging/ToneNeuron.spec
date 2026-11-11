# -*- mode: python ; coding: utf-8 -*-
import os
import sys

from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821 - provided by PyInstaller

hiddenimports = collect_submodules("tone_neuron") + [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
]

a = Analysis(
    [os.path.join(SPECPATH, "desktop_entry.py")],  # noqa: F821
    pathex=[ROOT],
    binaries=[],
    datas=[(os.path.join(ROOT, "tone_neuron", "data"), "tone_neuron/data")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest", "fasttext"],
    noarchive=False,
)

pyz = PYZ(a.pure)

# File-version resource is Windows-only; PyInstaller ignores it elsewhere.
version_file = os.path.join(SPECPATH, "version_info.txt") if sys.platform == "win32" else None  # noqa: F821

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ToneNeuron",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=version_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="ToneNeuron",
)

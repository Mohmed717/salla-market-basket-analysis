# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Salla market basket analysis application.

The spec is used instead of command line flags so the same build works on
Windows and Linux (the ``--add-data`` separator differs between platforms).
"""

import os

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.getcwd())

datas = [
    (os.path.join(ROOT, "data"), "data"),
    (os.path.join(ROOT, "assets"), "assets"),
]
binaries = []
hiddenimports = ["arabic_reshaper", "bidi", "matplotlib.backends.backend_qtagg"]

pkg_datas, pkg_binaries, pkg_hidden = collect_all("matplotlib")
datas += pkg_datas
binaries += pkg_binaries
hiddenimports += pkg_hidden

icon_path = os.path.join(ROOT, "assets", "icon.ico")
if not os.path.exists(icon_path):
    icon_path = None

analysis = Analysis(
    ["main.py"],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PySide6", "PyQt5"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Salla-MarketBasket",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Salla-MarketBasket",
)

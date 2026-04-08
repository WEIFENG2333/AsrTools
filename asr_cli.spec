# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['requests', 'urllib3', 'chardet', 'idna', 'certifi', '_ssl', 'ssl', '_hashlib', '_socket', 'http.client', 'urllib.request', 'urllib.parse', 'urllib.error', '_ctypes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'qfluentwidgets', 'torch', 'torchvision', 'torchaudio', 'pandas', 'scipy', 'yaml', 'setuptools', 'pywin32', 'Pythonwin', 'markupsafe', 'PIL', 'dateutil', 'pytz', 'google'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='asr_cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='asr_cli',
)

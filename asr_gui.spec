# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['asr_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'qfluentwidgets', 'requests', 'urllib3', 'chardet', 'idna', 'certifi', '_ssl', 'ssl', '_hashlib', '_socket', 'http.client', 'urllib.request', 'urllib.parse', 'urllib.error', '_ctypes'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'torchaudio', 'pandas', 'scipy', 'yaml', 'setuptools', 'pywin32', 'Pythonwin', 'markupsafe', 'PIL', 'dateutil', 'pytz', 'google'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='asr_gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=False,
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
    name='asr_gui',
)

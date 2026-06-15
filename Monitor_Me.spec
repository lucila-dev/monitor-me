# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Monitor Me macOS app."""

from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    ['main.py'],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'assets' / 'app_icon.png'), 'assets'),
        (str(root / 'assets' / 'AppIcon.icns'), 'assets'),
    ],
    hiddenimports=[
        'collectors',
        'collectors.cpu',
        'collectors.memory',
        'collectors.disk',
        'collectors.network',
        'collectors.processes',
        'collectors.battery',
        'collectors.system_info',
        'services',
        'services.monitor',
        'services.database',
        'services.alerts',
        'ui',
        'ui.main_window',
        'ui.overview',
        'ui.processes',
        'ui.performance',
        'ui.storage',
        'ui.network',
        'ui.system_page',
        'ui.theme',
        'ui.widgets',
        'models',
        'utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Monitor Me',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / 'assets' / 'AppIcon.icns'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Monitor Me',
)

app = BUNDLE(
    coll,
    name='Monitor Me.app',
    icon=str(root / 'assets' / 'AppIcon.icns'),
    bundle_identifier='com.monitorme.app',
    info_plist={
        'CFBundleName': 'Monitor Me',
        'CFBundleDisplayName': 'Monitor Me',
        'CFBundleGetInfoString': 'Monitor Me — system monitor',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '12.0',
    },
)

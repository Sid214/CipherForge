# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['cipherforge.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('cipherforge/assets', 'cipherforge/assets'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtSvg',
        'PyQt6.sip',
        'cipherforge',
        'cipherforge.core',
        'cipherforge.core.analyzer',
        'cipherforge.core.generator',
        'cipherforge.core.rules',
        'cipherforge.gui',
        'cipherforge.gui.app_qt',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CipherForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='cipherforge/assets/app_icon.ico',
)

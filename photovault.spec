# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

added_datas = [
    ('dist', 'dist'),
    ('assets', 'assets'),
]

hidden_imports = [
    'bottle',
    'webview',
    'clr_loader',
    'pythonnet',
    'cv2',
    'PIL',
    'PIL.Image',
    'PIL.ImageOps',
    'PIL.WebPImagePlugin',
    'PIL._webp',
    'PIL.JpegImagePlugin',
    'PIL.PngImagePlugin',
    'PIL.BmpImagePlugin',
    'PIL.TiffImagePlugin',
    'PIL.GifImagePlugin',
    'imagehash',
    'scipy',
    'scipy.fftpack',
    'scipy.fft',
    'pywt',
    'send2trash',
    'keyring',
    'keyring.backends',
    'keyring.backends.Windows',
    'numpy',
    'tkinter',
    'tkinter.filedialog',
    'wsgiref',
    'wsgiref.simple_server',
    'socketserver',
]

a = Analysis(
    ['backend/app.py'],
    pathex=['backend', '.'],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'torch', 'torchvision', 'tensorflow', 'notebook'],
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
    name='PhotoVault',
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
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PhotoVault',
)


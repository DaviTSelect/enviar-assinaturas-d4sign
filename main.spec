# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

# Windows Store Python instala DLLs em Program Files\WindowsApps\ (virtualizado).
# O PyInstaller não as coleta automaticamente; localizamos o diretório real via glob.
import glob, sys
_ver = f"{sys.version_info.major}{sys.version_info.minor}"
_base_dir = Path(sys._base_executable).parent
if not (_base_dir / f'python{_ver}.dll').exists():
    _wa = sorted(glob.glob(
        f"C:/Program Files/WindowsApps/PythonSoftwareFoundation.Python."
        f"{sys.version_info.major}.{sys.version_info.minor}_*"
    ), reverse=True)
    _base_dir = next((Path(d) for d in _wa if (Path(d) / f'python{_ver}.dll').exists()), _base_dir)
_dll_names = [f'python{_ver}.dll', 'python3.DLL', 'VCRUNTIME140.dll', 'vcruntime140_1.dll']
_extra_binaries = [(str(_base_dir / d), '.') for d in _dll_names if (_base_dir / d).exists()]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=_extra_binaries,
    datas=[],
    hiddenimports=[
        'pyexpat',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtSvg',
        'PySide6.QtXml',
    ] + collect_submodules('selenium'),
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
    name='EnviarAssinaturas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo_facto.ico'],
)

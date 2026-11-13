# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports=(collect_submodules('attstudio')+collect_submodules('attgames')+
               collect_submodules('uvicorn')+collect_submodules('scenedetect'))
datas=[('../attstudio/static','attstudio/static'),('../brand','brand')]
datas+=collect_data_files('espeakng_loader')

a=Analysis(
    ['windows_entry.py'],
    pathex=['..'],
    binaries=[('bin/ffmpeg.exe','bin'),('bin/ffprobe.exe','bin')],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=['attpublish','googleapiclient','google_auth_httplib2','pytest','httpx'],
    noarchive=False,
)
pyz=PYZ(a.pure)
exe=EXE(
    pyz,a.scripts,[],exclude_binaries=True,
    name='ATT-DOS-GAMES-Studio',
    debug=False,bootloader_ignore_signals=False,strip=False,upx=False,
    console=False,disable_windowed_traceback=True,
)
coll=COLLECT(exe,a.binaries,a.datas,strip=False,upx=False,
             name='ATT-DOS-GAMES-Studio')

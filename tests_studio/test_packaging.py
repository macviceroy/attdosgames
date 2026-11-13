import os
import sys
from pathlib import Path

import attstudio.runtime as runtime
from attstudio.runtime import default_data_dir, executable, resource, worker_command


def test_source_runtime_paths_and_worker(tmp_path, monkeypatch):
    monkeypatch.delenv('ATT_STUDIO_DIR',raising=False)
    assert resource('attstudio','static','index.html').is_file()
    assert resource('brand','DejaVuSans-Bold.ttf').is_file()
    assert Path(executable('ffmpeg')).is_file()
    assert worker_command(tmp_path,'a'*32)[:3]==[sys.executable,'-m','attstudio.worker']
    assert default_data_dir().name=='studio-data'


def test_frozen_windows_data_and_worker(tmp_path,monkeypatch):
    monkeypatch.setattr(sys,'frozen',True,raising=False)
    monkeypatch.setattr(runtime,'is_frozen_windows',lambda:True)
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'Local App Data'))
    command=worker_command(tmp_path/'dados com espaço','b'*32)
    assert command[0]==sys.executable and command[1]=='--worker'
    assert default_data_dir()==tmp_path/'Local App Data'/'ATT DOS GAMES Studio'/'data'


def test_environment_data_override(tmp_path,monkeypatch):
    configured=tmp_path/'projetos personalizados'
    monkeypatch.setenv('ATT_STUDIO_DIR',str(configured))
    assert default_data_dir()==configured.resolve()

"""Offline smoke test used by the packaged Windows executable."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .media import digest, ff, inspect_upload, probe
from .models import Project
from .runtime import executable, resource, worker_command
from .store import Store, uid


def self_test() -> None:
    assert resource('attstudio','static','index.html').is_file()
    assert resource('brand','DejaVuSans-Bold.ttf').is_file()
    with tempfile.TemporaryDirectory(prefix='att-studio-self-test-') as temporary:
        root=Path(temporary)
        source=root/'source.mp4'
        ff(['-f','lavfi','-i','testsrc2=s=320x240:r=30:d=1.5',
            '-f','lavfi','-i','sine=frequency=440:duration=1.5',
            '-c:v','libx264','-preset','ultrafast','-c:a','aac','-t','1.5',str(source)],timeout=90)
        info=inspect_upload(source,'video')
        db=Store(root/'data')
        asset_id=uid();folder=db.root/'assets'/asset_id;folder.mkdir()
        destination=folder/'source.mp4';shutil.copy2(source,destination)
        db.add_asset({'id':asset_id,'name':'self-test.mp4','extension':'.mp4','kind':'video',
                      'bytes':destination.stat().st_size,'rights':'procedural self-test fixture',
                      'sha256':digest(destination),**info})
        project=Project(name='Windows self-test',title='ATT Studio',
                        clips=[{'asset':asset_id,'start':0,'end':1}])
        job,_=db.enqueue('render',{'project_id':'self-test','project':project.model_dump()})
        result=subprocess.run(worker_command(db.root,job['id']),timeout=180)
        completed=db.job(job['id'])
        output=db.root/'jobs'/job['id']/'video.mp4'
        if result.returncode or completed['state']!='completed' or not output.is_file():
            raise RuntimeError(f"Self-test falhou: {completed['state']} {completed.get('error')}")
        media=probe(output);video=next(s for s in media['streams'] if s['codec_type']=='video')
        assert (video['width'],video['height'])==(1080,1920)
        print(json.dumps({'ok':True,'ffmpeg':executable('ffmpeg'),'ffprobe':executable('ffprobe'),
                          'worker':'frozen' if getattr(sys,'frozen',False) else 'python',
                          'output_sha256':digest(output)},ensure_ascii=False))

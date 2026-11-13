import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from attstudio.api import create_app
from attstudio.store import Store
from attstudio.models import Project, Cue
from attstudio.captions import parse_srt, srt, ass
from attstudio.commands import propose
from attstudio.media import ff, input_args, inspect_upload, digest, validate_project

@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path/'store')) as c:yield c

@pytest.fixture
def video(tmp_path):
    path=tmp_path/'real.mp4'
    ff(['-f','lavfi','-i','testsrc2=s=320x240:r=30:d=3','-f','lavfi','-i','sine=frequency=440:duration=3','-c:v','libx264','-preset','ultrafast','-c:a','aac','-t','3',str(path)])
    return path

def upload(client,path,kind='video'):
    r=client.post('/api/assets',params={'filename':path.name,'kind':kind,'rights':'Mídia procedural original CC0 de teste'},content=path.read_bytes(),headers={'X-ATT-Studio':'1'})
    assert r.status_code==200,r.text
    return r.json()

def project(asset):
    return Project(name='Projeto de teste',clips=[{'asset':asset,'start':0,'end':2}])

def test_upload_probe_thumbnail_range(client,video):
    a=upload(client,video)
    assert a['width']==320 and a['height']==240 and abs(a['duration']-3)<.1
    assert client.get('/api/assets/'+a['id']+'/thumbnail').headers['content-type']=='image/jpeg'
    response=client.get('/api/assets/'+a['id']+'/file',headers={'Range':'bytes=0-31'})
    assert response.status_code==206 and len(response.content)==32

def test_csrf_host_rights_and_path_controls(client,video):
    assert client.post('/api/publish').status_code==403
    assert client.post('/api/publish',headers={'X-ATT-Studio':'1','Origin':'https://evil.example'}).status_code==403
    assert client.post('/api/publish',headers={'X-ATT-Studio':'1'}).status_code==423
    assert client.get('/api/projects',headers={'Host':'evil.example'}).status_code==400
    assert client.post('/api/assets',params={'filename':'x.mp4','kind':'video','rights':''},content=b'x',headers={'X-ATT-Studio':'1'}).status_code==422
    assert client.get('/api/assets/no-such-id/file').status_code==404

def test_invalid_file_cleanup(client, tmp_path):
    path=tmp_path/'fake.mp4';path.write_bytes(b'not a video')
    response=client.post('/api/assets',params={'filename':path.name,'kind':'video','rights':'Original autorizado'},content=path.read_bytes(),headers={'X-ATT-Studio':'1'})
    assert response.status_code==422
    assert not list((client.app.state.db.root/'incoming').iterdir())


def test_revisions_conflicts_integrity(client,video):
    a=upload(client,video);p=project(a['id']).model_dump()
    h={'X-ATT-Studio':'1'}
    r=client.post('/api/projects',json=p,headers=h).json()
    p['title']='Outro título'
    change={'revision':r['revision'],'project':p}
    assert client.put('/api/projects/'+r['id'],json=change,headers=h).status_code==200
    assert client.put('/api/projects/'+r['id'],json=change,headers=h).status_code==409
    assert len(client.get('/api/projects/'+r['id']+'/history').json())==2
    db=client.app.state.db;db.path(a['id']).write_bytes(b'corrupt')
    assert client.post('/api/projects',json=p,headers=h).status_code==409

def test_timeline_and_injection_validation():
    with pytest.raises(ValueError):Cue(start=0,end=1,text='{\\pos(0,0)}injetado')
    with pytest.raises(ValueError):Cue(start=float('nan'),end=1,text='x')
    with pytest.raises(ValueError):project('../bad')
    p=project('a'*32);p.captions.cues=[Cue(start=0,end=1,text='Olá, Brasil!')]
    assert parse_srt(srt(p.captions.cues))==p.captions.cues
    assert 'Olá, Brasil!' in ass(p)
    with pytest.raises(ValueError):Project.model_validate({**p.model_dump(),'clips':[{'asset':'a'*32,'start':4,'end':3}]})

def test_idempotency_and_recovery(tmp_path):
    from attstudio.jobs import Queue
    db=Store(tmp_path);a,created=db.enqueue('render',{'x':1});b,again=db.enqueue('render',{'x':1})
    assert created and not again and a['id']==b['id']
    q=Queue(db);q.recover();assert db.job(a['id'])['state']=='interrupted';q.close()

def test_command_proposals_do_not_mutate():
    p=Project(name='x',clips=[{'asset':'a'*32,'start':0,'end':20}])
    result=propose(p,'Corte os primeiros 5 segundos.')
    assert p.clips[0].start==0 and result['proposal']['clips'][0]['start']==5 and not result['applied']
    with pytest.raises(ValueError):propose(p,'execute rm -rf /')

def test_voice_clipping_guard(client,video):
    a=upload(client,video);p=project(a['id']);from attstudio.models import Track
    p.narration=Track(asset=a['id'])
    with pytest.raises(ValueError):validate_project(client.app.state.db,p)

def test_artifact_whitelist(client):
    db=client.app.state.db;j,_=db.enqueue('render',{});db.state(j['id'],'completed',{})
    assert client.get('/api/jobs/'+j['id']+'/files/worker.log').status_code==404

def test_transcription_requires_local_model(client,video,monkeypatch):
    monkeypatch.delenv('ATT_WHISPER_MODEL',raising=False)
    a=upload(client,video)
    assert client.post('/api/transcribe',json={'asset':a['id']},headers={'X-ATT-Studio':'1'}).status_code==409

def test_original_music_has_distinct_audio_and_rights(client):
    assets=[]
    for style in ['synthwave','eletronica','lofi']:
        r=client.post('/api/music/'+style,headers={'X-ATT-Studio':'1'})
        assert r.status_code==200,r.text
        a=r.json();assert a['audio'] and a['bpm']>0 and 'CC0' in a['rights'];assets.append(a)
    assert len({a['sha256'] for a in assets})==3
    assert client.post('/api/music/unknown',headers={'X-ATT-Studio':'1'}).status_code==409

def test_cancel_queued_and_retry(client,video):
    from attstudio.worker import execute
    db=client.app.state.db
    j,_=db.enqueue('analyze',{'asset':'a'*32,'seconds':3})
    client.app.state.queue.cancel(j['id'])
    execute(db.root,j['id'])
    assert db.job(j['id'])['state']=='cancelled'
    assert not list((db.root/'jobs'/j['id']).glob('*.mp4'))


def test_motion_title_validation(tmp_path):
    from attstudio.motion import create
    with pytest.raises(ValueError):create('x'*71,tmp_path/'video.mp4')

def test_concurrent_job_requests_share_id(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    db=Store(tmp_path)
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs=list(pool.map(lambda _:db.enqueue('render',{'same':'payload'}),range(16)))
    assert len({job['id'] for job,_ in jobs})==1
    assert sum(created for _,created in jobs)==1

def test_recovery_does_not_steal_live_worker(tmp_path):
    from filelock import FileLock
    from attstudio.jobs import Queue
    db=Store(tmp_path);j,_=db.enqueue('render',{'x':1});db.state(j['id'],'running')
    queue=Queue(db)
    lock=FileLock(str(db.root/'jobs'/(j['id']+'.lock')))
    with lock:
        queue.recover()
        assert db.job(j['id'])['state']=='running'
        db.state(j['id'],'interrupted')
        with pytest.raises(ValueError,match='ainda possui'):queue.retry(j['id'])
    queue.recover()
    assert db.job(j['id'])['state']=='interrupted'
    queue.close()

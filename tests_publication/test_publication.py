import json
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

from attpublish.adapters import LocalSimulator, SimulationUncertain, ThumbnailDenied
from attpublish.api import app
from attpublish.media import prepare, sha256
from attpublish.models import PublicationError, SCOPES, Submission
from attpublish.service import PublicationService
from attpublish.store import PublicationStore


@pytest.fixture(scope='session')
def media(tmp_path_factory):
    folder = tmp_path_factory.mktemp('licensed-generated-media')
    video, cover = folder/'input.mp4', folder/'cover.png'
    subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=0x0B0B14:s=1080x1920:r=30',
                    '-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','3',
                    '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',
                    '-movflags','+faststart','-threads','2',str(video)],check=True)
    Image.new('RGBA',(1080,1920),(255,0,122,160)).save(cover)
    return video,cover


@pytest.fixture(autouse=True)
def offline(monkeypatch,tmp_path):
    monkeypatch.setenv('ATT_PUBLISH_DATA_DIR',str(tmp_path/'publication'))
    monkeypatch.delenv('ATT_PUBLISH_API_KEY',raising=False)
    def fail(*args,**kwargs):
        raise AssertionError('Rede proibida no dry-run')
    monkeypatch.setattr(socket.socket,'connect',fail)


def payload(media, platforms=None, capability='unknown'):
    platforms = platforms or ['instagram','youtube']
    return {'mode':'dry-run','video':str(media[0]),'cover':str(media[1]),'title':'Teste ATT DOS GAMES',
            'description':'Demonstração original de teste.','hashtags':['#ATTDOSGAMES','Games'],
            'platforms':platforms,'authentication':{
                p:{'simulated':True,'subject':'sim_'+p,'scopes':sorted(SCOPES[p]),
                   'expires_at':(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(),
                   'thumbnail_capability':capability} for p in platforms}}


@pytest.fixture
def prepared(media,tmp_path_factory):
    # Actual file validation/FFmpeg/Pillow, not fabricated ffprobe responses.
    return prepare(*media,tmp_path_factory.mktemp('prepared'))


def test_two_official_adapters_end_to_end(media,tmp_path):
    gateway=LocalSimulator()
    service=PublicationService(tmp_path,gateway)
    result=service.dry_run(Submission.model_validate(payload(media)))
    assert result['provider_requests_sent']==0 and result['published'] is False
    assert result['real_authentication_verified'] is False
    assert {r['platform'] for r in result['results']}=={'instagram','youtube'}
    for row in result['results']:
        assert row['state']=='simulated_confirmed'
        assert row['remote_id'] is None and row['remote_url'] is None
        assert row['receipt']['real_confirmation'] is False
        assert all(i.startswith('sim_') for i in row['simulated_ids'].values())
        assert row['plan']['authentication']['real_authentication_verified'] is False
    instagram=next(r for r in result['results'] if r['platform']=='instagram')
    image=Path(instagram['plan']['cover']['local_file'])
    with Image.open(image) as jpg:
        assert jpg.format=='JPEG' and jpg.size==(1080,1920)
        assert jpg.info['icc_profile']
    body=instagram['plan']['steps'][0]['body']
    assert body['media_type']=='REELS' and 'cover_url' in body and 'thumb_offset' not in body
    assert all(c['operation']!='thumbnail' for c in gateway.calls)


@pytest.mark.parametrize('capability,expected',[('available','simulated_custom_png'),('unknown','platform_generated_thumbnail'),('unavailable','platform_generated_thumbnail')])
def test_youtube_thumbnail_capabilities(media,tmp_path,capability,expected):
    gateway=LocalSimulator()
    result=PublicationService(tmp_path,gateway).dry_run(Submission.model_validate(payload(media,['youtube'],capability)))
    row=result['results'][0]
    assert row['receipt']['thumbnail']==expected
    operations=[c['operation'] for c in gateway.calls]
    if capability=='available':
        assert operations.index('thumbnail')>operations.index('video_status')
    else:
        assert 'thumbnail' not in operations


def test_youtube_thumbnail_permission_fallback(media,tmp_path):
    class Denied(LocalSimulator):
        def call(self,platform,operation,job_id):
            if operation=='thumbnail': raise ThumbnailDenied('simulated 403')
            return super().call(platform,operation,job_id)
    result=PublicationService(tmp_path,Denied()).dry_run(Submission.model_validate(payload(media,['youtube'],'available')))
    assert result['results'][0]['receipt']['thumbnail']=='platform_generated_thumbnail_permission_denied'
    assert result['results'][0]['state']=='simulated_confirmed'


def test_processing_must_finish_before_thumbnail(media,tmp_path):
    class Processing(LocalSimulator):
        def call(self,p,op,job):
            r=super().call(p,op,job)
            if op=='video_status': r['processingStatus']='processing'
            return r
    gateway=Processing()
    row=PublicationService(tmp_path,gateway).dry_run(Submission.model_validate(payload(media,['youtube'],'available')))['results'][0]
    assert row['state']=='simulation_unknown'
    assert not any(c['operation']=='thumbnail' for c in gateway.calls)


def test_idempotent_no_second_upload(media,tmp_path):
    gateway=LocalSimulator();service=PublicationService(tmp_path,gateway)
    request=Submission.model_validate(payload(media))
    first=service.dry_run(request)
    calls=len(gateway.calls)
    second=service.dry_run(request)
    assert [r['id'] for r in first['results']]==[r['id'] for r in second['results']]
    assert all(r['reused'] for r in second['results'])
    assert len(gateway.calls)==calls


def test_conflicting_metadata_blocks_reupload(media,tmp_path):
    gateway=LocalSimulator();service=PublicationService(tmp_path,gateway)
    data=payload(media)
    service.dry_run(Submission.model_validate(data));calls=len(gateway.calls)
    data['title']='Outro título para mesmo vídeo'
    with pytest.raises(PublicationError,match='Mesmo vídeo'):
        service.dry_run(Submission.model_validate(data))
    assert len(gateway.calls)==calls


def test_ambiguous_confirmation_reconcile_without_reupload(media,tmp_path):
    class Timeout(LocalSimulator):
        def call(self,p,op,job):
            if op=='video_status': raise SimulationUncertain('timeout after simulated acceptance')
            return super().call(p,op,job)
    gateway=Timeout();service=PublicationService(tmp_path,gateway)
    submission=Submission.model_validate(payload(media,['youtube']))
    first=service.dry_run(submission)['results'][0]
    assert first['state']=='simulation_unknown' and first['simulated_ids']['video_id'].startswith('sim_')
    calls=len(gateway.calls)
    again=service.dry_run(submission)['results'][0]
    assert again['id']==first['id'] and len(gateway.calls)==calls
    service.gateway=LocalSimulator()
    reconciled=service.reconcile(first['id'])
    assert reconciled['state']=='simulated_confirmed'
    assert all(c['operation']!='upload_video' for c in service.gateway.calls)


@pytest.mark.parametrize('case',['expired','naive_expiry','missing_scope','real_auth','token_field'])
def test_simulated_auth_rejections(media,tmp_path,case):
    data=payload(media,['youtube'])
    auth=data['authentication']['youtube']
    if case=='expired': auth['expires_at']='2000-01-01T00:00:00Z'
    elif case=='naive_expiry': auth['expires_at']='2099-01-01T00:00:00'
    elif case=='missing_scope': auth['scopes']=[]
    elif case=='real_auth': auth['simulated']=False
    else: auth['access_token']='DO_NOT_ECHO_THIS_FIXTURE'
    with pytest.raises((PublicationError,ValidationError)):
        PublicationService(tmp_path).dry_run(Submission.model_validate(data))
    with PublicationStore(tmp_path).connect() as db:
        assert db.execute('SELECT count(*) FROM dry_runs').fetchone()[0]==0


@pytest.mark.parametrize('case',['missing_file','invalid_mp4','bad_png','wrong_png_dimensions'])
def test_invalid_files(media,tmp_path,case):
    video,cover=media
    if case=='missing_file': video=tmp_path/'missing.mp4'
    elif case=='invalid_mp4':
        video=tmp_path/'invalid.mp4';video.write_text('not a movie')
    elif case=='bad_png':
        cover=tmp_path/'corrupt.png';cover.write_text('not an image')
    else:
        cover=tmp_path/'small.png';Image.new('RGB',(100,100)).save(cover)
    with pytest.raises(PublicationError): prepare(video,cover,tmp_path/'assets')


def test_prepared_input_integrity_and_original_preserved(media,tmp_path):
    original=[sha256(p) for p in media]
    assets=prepare(*media,tmp_path)
    (Path(assets['directory'])/'video.mp4').write_bytes(b'tampered')
    with pytest.raises(PublicationError,match='alterados'): prepare(*media,tmp_path)
    assert [sha256(p) for p in media]==original


@pytest.mark.parametrize('case',['blank_title','long_title','youtube_bytes','instagram_caption','hashtag','live_mode','unsupported_metricool'])
def test_invalid_metadata(media,case):
    data=payload(media)
    if case=='blank_title': data['title']='   '
    elif case=='long_title': data['title']='x'*101
    elif case=='youtube_bytes':
        data=payload(media,['youtube']);data['description']='á'*2501
    elif case=='instagram_caption': data['description']='x'*2200
    elif case=='hashtag': data['hashtags']=['invalid tag']
    elif case=='live_mode': data['mode']='live'
    else: data['platforms']=['metricool']
    with pytest.raises(ValidationError): Submission.model_validate(data)


def candidate(platform='youtube',account='sim_a',fingerprint='same'):
    return dict(platform=platform,account=account,source_video_sha256='a'*64,fingerprint=fingerprint,plan={})


def test_atomic_concurrent_reservation(tmp_path):
    store=PublicationStore(tmp_path)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:store.reserve([candidate()])[0],range(8)))
    assert sum(created for job,created in results)==1
    assert len({job for job,created in results})==1


def test_multi_platform_conflict_rolls_back(tmp_path):
    store=PublicationStore(tmp_path)
    store.reserve([candidate('instagram')])
    with pytest.raises(PublicationError):
        store.reserve([candidate('youtube'),candidate('instagram',fingerprint='changed')])
    with store.connect() as db:
        assert db.execute('SELECT count(*) FROM dry_runs').fetchone()[0]==1


def test_live_disabled_direct_and_api(tmp_path):
    with pytest.raises(PublicationError,match='desabilitada'): PublicationService(tmp_path).live()
    client=TestClient(app)
    assert client.post('/publish').status_code==423
    assert client.get('/dry-runs/missing').status_code==404


def test_api_offline_and_auth(media,monkeypatch):
    client=TestClient(app)
    response=client.post('/dry-runs',json=payload(media,['youtube']))
    assert response.status_code==200
    row=response.json()['results'][0]
    assert client.get('/dry-runs/'+row['id']).json()['state']=='simulated_confirmed'
    key='EXAMPLE_API_TEST_KEY_'+'x'*32
    monkeypatch.setenv('ATT_PUBLISH_API_KEY',key)
    assert client.get('/dry-runs/'+row['id']).status_code==401
    assert client.get('/dry-runs/'+row['id'],headers={'Authorization':'Bearer '+key}).status_code==200


def test_api_rejects_secrets_without_echoing(media):
    data=payload(media,['youtube'])
    data['authentication']['youtube']['access_token']='DO_NOT_ECHO_THIS_FIXTURE'
    response=TestClient(app).post('/dry-runs',json=data)
    assert response.status_code==422
    assert 'DO_NOT_ECHO_THIS_FIXTURE' not in response.text


def test_google_sdk_compiles_upload_processing_and_thumbnail(media,tmp_path):
    row=PublicationService(tmp_path).dry_run(Submission.model_validate(payload(media,['youtube'],'available')))['results'][0]
    sdk=row['plan']['sdk_validation']
    assert sdk['static_discovery'] is True and sdk['http_attempts']==0
    assert len(sdk['requests'])==3
    assert 'uploadType=resumable' in sdk['requests'][0]['uri']
    assert '/videos?' in sdk['requests'][1]['uri']
    assert '/thumbnails/set?' in sdk['requests'][2]['uri']
    assert all(r['executed'] is False for r in sdk['requests'])


def test_remote_api_requires_authentication():
    client=TestClient(app,client=('203.0.113.10',1234))
    assert client.post('/publish').status_code==403


def test_simulator_cannot_claim_real_publication(tmp_path):
    store=PublicationStore(tmp_path)
    job_id,_=store.reserve([candidate()])[0]
    with pytest.raises(PublicationError,match='real'):
        store.finish(job_id,{'state':'published','published':True,'real_confirmation':True,'remote_id':'real','remote_url':None})


def test_incomplete_prepared_manifest_rejected(media,tmp_path):
    assets=prepare(*media,tmp_path)
    path=Path(assets['directory'])/'manifest.json'
    data=json.loads(path.read_text());data['hashes']={};path.write_text(json.dumps(data))
    with pytest.raises(PublicationError,match='incompleto'):
        prepare(*media,tmp_path)


def test_unexpected_simulator_failure_is_persisted_without_secrets(media,tmp_path):
    class Broken(LocalSimulator):
        def call(self,p,op,job): raise RuntimeError('DO_NOT_ECHO_THIS_FIXTURE')
    row=PublicationService(tmp_path,Broken()).dry_run(Submission.model_validate(payload(media,['youtube'])))['results'][0]
    assert row['state']=='simulation_unknown'
    assert row['receipt']['error_type']=='RuntimeError'
    assert 'DO_NOT_ECHO_THIS_FIXTURE' not in json.dumps(row)


def test_non_ascii_authorization_is_rejected_cleanly(monkeypatch):
    monkeypatch.setenv('ATT_PUBLISH_API_KEY','EXAMPLE_API_TEST_KEY_'+'x'*32)
    response=TestClient(app).post('/publish',headers={'Authorization':b'Bearer \xc3\xa1'})
    assert response.status_code==401

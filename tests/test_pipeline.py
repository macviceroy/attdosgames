import json
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from attgames.api import app
from attgames.pipeline import validate, publish, produce, store
from attgames.editor import script, timestamp
from attgames.quality import inspect

@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv('ATT_DATA_DIR', str(tmp_path / 'data'))

@pytest.mark.parametrize('seconds', [10, 11, 35, 59, 60])
def test_timeline(seconds):
    scenes = script('Teste', seconds)
    assert scenes[0]['start'] == 0
    assert scenes[-1]['end'] == seconds
    assert all(1 <= s['end']-s['start'] <= 3 for s in scenes)
    assert all(a['end'] == b['start'] for a,b in zip(scenes, scenes[1:]))
    assert 'rumores' in scenes[0]['text']

@pytest.mark.parametrize('theme,duration', [('',35), ('x'*65,35), ('jogo',9), ('jogo',61)])
def test_invalid(theme,duration):
    with pytest.raises(ValueError): validate(theme,duration)


def test_idempotent_production():
    with patch('attgames.pipeline.run_worker') as worker:
        first = produce('Tema', 35)
        second = produce('Tema', 35)
    assert first['id'] == second['id']
    assert worker.call_count == 1


def test_atomic_creation():
    db = store()
    def insert(i):
        return db.create({'id':str(i),'state':'queued'}, 'same')
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(insert, range(8)))
    assert sum(created for job,created in results) == 1
    assert len({job['id'] for job,created in results}) == 1


def test_publication_disabled():
    db = store()
    job,_ = db.create({'id':'a','state':'review_required'}, 'a')
    with pytest.raises(ValueError, match='Fase 1'): publish('a','instagram,youtube')
    assert db.events('a')[-1]['message'].startswith('Publicação bloqueada')


def test_missing_media_fails_closed(tmp_path):
    assert inspect(tmp_path,35)['technical_pass'] is False
    assert inspect(tmp_path,35)['publication_allowed'] is False


def test_api():
    client = TestClient(app)
    assert client.post('/produzir',json={'tema':'x','duracao':2}).status_code == 422
    assert client.get('/status/missing').status_code == 404
    assert client.post('/revisar/missing').status_code == 404
    assert client.post('/publicar/missing',json={}).status_code == 404


def test_worker_failure_recorded():
    with patch('attgames.pipeline.run_worker',side_effect=RuntimeError('TTS ausente')):
        job = produce('Teste',35)
    assert job['state'] == 'failed'
    assert 'TTS ausente' in job['error']

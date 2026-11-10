import hashlib
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit,parse_qs
from io import BytesIO
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from attpublish.handoff import Handoff,app
from attpublish.models import Submission,PublicationError
from tests_publication.test_publication import media,payload


def fixture(media,tmp_path,monkeypatch):
    monkeypatch.setenv('ATT_HANDOFF_DATA_DIR',str(tmp_path/'delivery'))
    service=Handoff()
    request=Submission.model_validate(payload(media))
    issued=service.issue(request,'https://delivery.example',60)
    return service,request,issued


def test_external_consumer_e2e(media,tmp_path,monkeypatch):
    service,request,issued=fixture(media,tmp_path,monkeypatch)
    # Simulated external client: full HTTP requests through ASGI, no real TLS/network.
    client=TestClient(app,base_url='https://delivery.example')
    response=client.get(issued['manifest_url'])
    assert response.status_code==200 and response.headers['cache-control']=='no-store, private'
    manifest=response.json()
    assert manifest['title']==request.title and manifest['description']==request.description
    assert manifest['hashtags']==request.hashtags and manifest['publication_allowed'] is False
    for name,entry in manifest['files'].items():
        result=client.get(entry['url'])
        assert result.status_code==200 and result.headers['content-type']==entry['mime_type']
        assert hashlib.sha256(result.content).hexdigest()==entry['sha256']
        if name=='cover':
            with Image.open(BytesIO(result.content)) as image: assert image.format=='PNG'
    assert service.issue(request,'https://delivery.example',60)==issued
    assert client.post('/publish').status_code in (404,405)


def test_signatures_revocation_and_renewal(media,tmp_path,monkeypatch):
    service,request,issued=fixture(media,tmp_path,monkeypatch)
    client=TestClient(app)
    assert client.get(issued['manifest_url']+'0').status_code==403
    assert client.get(issued['manifest_url'].replace('/manifest?','/video?')).status_code==403
    service.revoke(issued['id'])
    assert client.get(issued['manifest_url']).status_code==410
    with pytest.raises(PublicationError): service.issue(request,'https://delivery.example')
    renewed=service.issue(request,'https://delivery.example',60,renew=True)
    assert renewed['id']==issued['id'] and renewed['manifest_url']!=issued['manifest_url']
    assert client.get(issued['manifest_url']).status_code==403
    assert client.get(renewed['manifest_url']).status_code==200


def test_expiration(media,tmp_path,monkeypatch):
    service,request,issued=fixture(media,tmp_path,monkeypatch)
    row=service.row(issued['id'])
    service.clock=lambda:row['expires']
    with pytest.raises(PublicationError,match='expirada'):
        service.authorize(row['id'],'manifest',row['expires'],service.signature(row,'manifest'))


def test_tampered_asset_not_delivered(media,tmp_path,monkeypatch):
    service,request,issued=fixture(media,tmp_path,monkeypatch)
    client=TestClient(app);manifest=client.get(issued['manifest_url']).json()
    import json
    from pathlib import Path
    assets=json.loads(service.row(issued['id'])['assets'])
    (Path(assets['directory'])/'cover.png').write_bytes(b'changed')
    assert client.get(manifest['files']['cover']['url']).status_code==409


def test_invalid_origin_and_ttl(media,tmp_path,monkeypatch):
    service,request,issued=fixture(media,tmp_path,monkeypatch)
    for origin in ['http://example.com','https://user:password@example.com','https://example.com/?key=x']:
        with pytest.raises(PublicationError):service.issue(request,origin)
    with pytest.raises(PublicationError):service.issue(request,'https://delivery.example',7200)


def test_concurrent_issue_same_delivery(media,tmp_path,monkeypatch):
    service,request,issued=fixture(media,tmp_path,monkeypatch)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(lambda _:service.issue(request,'https://delivery.example',60),range(3)))
    assert all(result==issued for result in results)

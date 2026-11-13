import pytest

from attstudio.automation import script_from_transcript
from attstudio.importers import validate_url


def test_script_is_based_on_transcript_and_requires_review():
    result=script_from_transcript('Teste ATT','Essa novidade muda tudo! O vídeo mostra três momentos importantes. O último merece atenção.')
    assert result['hook']=='Essa novidade muda tudo!'
    assert 'três momentos' in result['script']
    assert result['review_required'] is True
    assert result['source'].startswith('transcrição')


@pytest.mark.parametrize('url',[
    'https://www.youtube.com/watch?v=abc',
    'https://youtu.be/abc',
    'https://www.instagram.com/reel/abc/',
    'https://www.tiktok.com/@att/video/1',
])
def test_authorized_video_hosts(url):
    assert validate_url(url)==url


@pytest.mark.parametrize('url',[
    'http://youtube.com/watch?v=abc',
    'https://youtube.com.evil.example/video',
    'file:///etc/passwd',
    'https://user:pass@youtube.com/video',
])
def test_url_import_rejects_unsafe_sources(url):
    with pytest.raises(ValueError):validate_url(url)

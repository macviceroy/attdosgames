"""Compile request shapes with Google's official SDK; executing is impossible."""
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .models import PublicationError


class NoNetworkHttp:
    def __init__(self):
        self.attempts = 0

    def request(self, *args, **kwargs):
        self.attempts += 1
        raise PublicationError('network_disabled', 'SDK HTTP desabilitado no dry-run')

    def close(self):
        pass


def compile_requests(assets, steps):
    transport = NoNetworkHttp()
    # http supplied explicitly: no ADC, token lookup or interactive OAuth.
    # Static discovery is packaged with the SDK, never fetched over HTTP.
    client = build('youtube', 'v3', http=transport, static_discovery=True, cache_discovery=False)
    directory = Path(assets['directory'])
    streams = []
    requests = []
    try:
        for step in steps:
            if step['operation'] == 'upload_video':
                media = MediaFileUpload(str(directory / 'video.mp4'), mimetype='video/mp4', resumable=True, chunksize=1024 * 1024)
                streams.append(media.stream())
                request = client.videos().insert(part=','.join(step['part']), body=step['body'], media_body=media)
            elif step['operation'] == 'video_status':
                request = client.videos().list(part=','.join(step['part']), id='SIMULATED_VIDEO_ID')
            elif step['operation'] == 'thumbnail':
                media = MediaFileUpload(str(directory / 'cover.png'), mimetype='image/png', resumable=False)
                streams.append(media.stream())
                request = client.thumbnails().set(videoId='SIMULATED_VIDEO_ID', media_body=media)
            else:
                raise PublicationError('unsupported_sdk_operation', 'Operação desconhecida pelo compilador SDK')
            requests.append({'operation': step['operation'], 'method': request.method, 'uri': request.uri,
                             'executed': False})
        if transport.attempts:
            raise PublicationError('network_disabled', 'SDK tentou HTTP durante compilação')
        return {'library': 'google-api-python-client', 'static_discovery': True,
                'real_authentication_verified': False, 'http_attempts': transport.attempts, 'requests': requests}
    except PublicationError:
        raise
    except Exception as error:
        # Do not echo raw SDK request/auth data in diagnostic messages.
        raise PublicationError('sdk_request_validation_failed', type(error).__name__) from error
    finally:
        for stream in streams:
            stream.close()
        client.close()

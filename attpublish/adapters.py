"""Official request plans + offline fixture adapters. Nothing sends HTTP."""
from .models import PublicationError

IG_DOC = 'https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/'
YT_DOC = 'https://developers.google.com/youtube/v3/docs/thumbnails/set'


class SimulationUncertain(RuntimeError):
    pass


class ThumbnailDenied(RuntimeError):
    pass


class LocalSimulator:
    """Deterministic fake provider. It contains no HTTP/SDK client or credentials."""
    def __init__(self):
        self.calls = []

    def call(self, platform, operation, job_id):
        self.calls.append({'platform': platform, 'operation': operation, 'job_id': job_id})
        suffix = job_id[:20]
        responses = {
            ('instagram', 'create_container'): {'id': 'sim_ig_container_' + suffix},
            ('instagram', 'container_status'): {'status_code': 'FINISHED'},
            ('instagram', 'publish_container'): {'id': 'sim_ig_media_' + suffix},
            ('instagram', 'media_status'): {'id': 'sim_ig_media_' + suffix, 'media_type': 'VIDEO'},
            ('youtube', 'upload_video'): {'id': 'sim_yt_video_' + suffix},
            ('youtube', 'video_status'): {'id': 'sim_yt_video_' + suffix,
                                         'processingStatus': 'succeeded', 'uploadStatus': 'processed', 'privacyStatus': 'private'},
            ('youtube', 'thumbnail'): {'thumbnail_applied': True},
        }
        try:
            return responses[(platform, operation)].copy()
        except KeyError as error:
            raise PublicationError('unsupported_simulated_operation', 'Operação não suportada pelo simulador') from error


def simulated_id(value):
    if not isinstance(value, str) or not value.startswith('sim_'):
        raise PublicationError('invalid_simulated_id', 'Simulador retornou identificador sem prefixo sim_')
    return value


class InstagramAdapter:
    platform = 'instagram'

    def plan(self, submission, assets, auth):
        return {'provider': 'instagram_api_instagram_login', 'mode': 'dry-run', 'documentation': IG_DOC,
                'api_host': 'https://graph.instagram.com', 'api_version': 'configure_supported_version_before_live',
                'account': auth['subject'], 'caption': submission.instagram_caption(),
                'cover': {'input': 'PNG', 'upload_format': 'JPEG', 'local_file': assets['directory'] + '/cover-instagram.jpg',
                          'requires_public_https': True, 'fallback_if_cover_unavailable': {'thumb_offset': 0},
                          'note': 'cover_url prevalece sobre thumb_offset; não enviar ambos'},
                'steps': [
                    {'operation': 'create_container', 'method': 'POST', 'resource': '/{ig_user_id}/media',
                     'body': {'media_type': 'REELS', 'caption': submission.instagram_caption(),
                              'video_url': {'binding': 'public_https_video_url'},
                              'cover_url': {'binding': 'public_https_jpeg_cover_url'}}},
                    {'operation': 'container_status', 'method': 'GET', 'resource': '/{container_id}',
                     'query': {'fields': 'status_code'}, 'requires': 'status_code=FINISHED'},
                    {'operation': 'publish_container', 'method': 'POST', 'resource': '/{ig_user_id}/media_publish',
                     'body': {'creation_id': {'binding': 'container_id'}}, 'requires': 'container FINISHED'},
                    {'operation': 'media_status', 'method': 'GET', 'resource': '/{media_id}',
                     'query': {'fields': 'id,permalink,media_type'}}],
                'live_blockers': ['real_oauth_not_verified', 'public_https_assets_missing', 'meta_api_version_not_selected',
                                  'human_editorial_and_rights_review_pending']}

    def simulate(self, row, gateway, progress):
        container = simulated_id(gateway.call(self.platform, 'create_container', row['id'])['id'])
        progress({'container_id': container})
        if gateway.call(self.platform, 'container_status', row['id']).get('status_code') != 'FINISHED':
            raise PublicationError('container_not_ready', 'Container simulado não terminou processamento')
        media = simulated_id(gateway.call(self.platform, 'publish_container', row['id'])['id'])
        progress({'media_id': media})
        return self.confirm(row, gateway, {'container_id': container, 'media_id': media})

    def confirm(self, row, gateway, ids):
        observed = gateway.call(self.platform, 'media_status', row['id'])
        media_id = ids.get('media_id')
        if not media_id:
            raise PublicationError('reconciliation_needed', 'Sem media_id simulado; não repetir envio')
        if simulated_id(observed.get('id')) != media_id or observed.get('media_type') != 'VIDEO':
            raise SimulationUncertain('Confirmação simulada inconsistente')
        return {'state': 'simulated_confirmed', 'simulated_ids': ids, 'confirmation': 'simulated_only',
                'real_confirmation': False, 'published': False, 'remote_id': None, 'remote_url': None,
                'thumbnail': 'simulated_jpeg_cover', 'provider_requests_sent': 0}


class YouTubeAdapter:
    platform = 'youtube'

    def plan(self, submission, assets, auth):
        capability = submission.authentication['youtube'].thumbnail_capability
        status = {'privacyStatus': 'private'}
        if submission.made_for_kids is not None:
            status['selfDeclaredMadeForKids'] = submission.made_for_kids
        steps = [
            {'operation': 'upload_video', 'sdk_method': 'youtube.videos.insert',
             'resumable': True, 'mime_type': 'video/mp4', 'part': ['snippet', 'status'],
             'body': {'snippet': {'title': submission.title, 'description': submission.youtube_description(),
                                  'tags': submission.hashtags, 'defaultLanguage': 'pt-BR'}, 'status': status}},
            {'operation': 'video_status', 'sdk_method': 'youtube.videos.list',
             'part': ['processingDetails', 'status'], 'id': {'binding': 'video_id'},
             'requires': 'processingDetails.processingStatus=succeeded; owner OAuth'}]
        if capability == 'available':
            steps.append({'operation': 'thumbnail', 'sdk_method': 'youtube.thumbnails.set',
                          'videoId': {'binding': 'video_id'}, 'mime_type': 'image/png',
                          'local_file': assets['directory'] + '/cover.png', 'requires': 'processing succeeded; verified/eligible channel'})
        from .youtube_sdk import compile_requests
        sdk_validation = compile_requests(assets, steps)
        return {'sdk_validation': sdk_validation, 'provider': 'youtube_data_api_v3', 'mode': 'dry-run', 'account': auth['subject'],
                'documentation': YT_DOC, 'steps': steps,
                'shorts': {'dedicated_upload_endpoint': False, 'classification': 'determined_by_youtube_not_guaranteed'},
                'thumbnail_policy': {'capability_fixture': capability, 'custom_requested': capability == 'available',
                                     'fallback': 'platform_generated_thumbnail',
                                     'manual_option': 'YouTube Studio desktop: PNG 9:16, somente se canal verificado/elegível',
                                     'processing_gate': 'succeeded', 'real_capability_verified': False},
                'live_blockers': ['real_oauth_not_verified', 'channel_thumbnail_capability_not_verified',
                                  'human_editorial_and_rights_review_pending'] +
                                 (['audience_classification_missing'] if submission.made_for_kids is None else [])}

    def simulate(self, row, gateway, progress):
        video = simulated_id(gateway.call(self.platform, 'upload_video', row['id'])['id'])
        progress({'video_id': video})
        return self.confirm(row, gateway, {'video_id': video})

    def confirm(self, row, gateway, ids):
        video_id = ids.get('video_id')
        if not video_id:
            raise PublicationError('reconciliation_needed', 'Sem video_id simulado; não repetir upload')
        observed = gateway.call(self.platform, 'video_status', row['id'])
        if (simulated_id(observed.get('id')) != video_id or observed.get('processingStatus') != 'succeeded'
                or observed.get('uploadStatus') != 'processed' or observed.get('privacyStatus') != 'private'):
            raise SimulationUncertain('Processamento/confirmação simulada pendente ou inconsistente')
        thumbnail = 'platform_generated_thumbnail'
        if row['plan']['thumbnail_policy']['custom_requested']:
            try:
                if gateway.call(self.platform, 'thumbnail', row['id']).get('thumbnail_applied') is True:
                    thumbnail = 'simulated_custom_png'
            except ThumbnailDenied:
                thumbnail = 'platform_generated_thumbnail_permission_denied'
        return {'state': 'simulated_confirmed', 'simulated_ids': ids, 'confirmation': 'simulated_only',
                'real_confirmation': False, 'published': False, 'remote_id': None, 'remote_url': None,
                'thumbnail': thumbnail, 'provider_requests_sent': 0}


ADAPTERS = {'instagram': InstagramAdapter(), 'youtube': YouTubeAdapter()}

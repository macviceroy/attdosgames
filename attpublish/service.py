import hashlib
import json
import os
from .adapters import ADAPTERS, LocalSimulator, SimulationUncertain
from .media import prepare
from .models import PublicationError, Submission
from .store import PublicationStore


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class PublicationService:
    def __init__(self, root=None, gateway=None):
        self.store = PublicationStore(root or os.environ.get('ATT_PUBLISH_DATA_DIR', 'publication-data'))
        self.gateway = gateway if gateway is not None else LocalSimulator()

    def dry_run(self, submission: Submission):
        # Validate every fixture before doing expensive media processing/reserving.
        auth = {platform: submission.authentication[platform].validate_for(platform) for platform in submission.platforms}
        assets = prepare(submission.video, submission.cover, self.store.root)
        candidates = []
        for platform in submission.platforms:
            adapter = ADAPTERS[platform]
            payload = {'video': assets['validation']['source_video_sha256'],
                       'cover': assets['validation']['source_cover_sha256'], 'title': submission.title,
                       'description': submission.description, 'hashtags': submission.hashtags,
                       'made_for_kids': submission.made_for_kids,
                       'thumbnail_capability': submission.authentication[platform].thumbnail_capability}
            plan = adapter.plan(submission, assets, auth[platform])
            plan['authentication'] = auth[platform]
            plan['assets'] = assets
            candidates.append({'platform': platform, 'account': auth[platform]['subject'],
                               'source_video_sha256': payload['video'], 'fingerprint': fingerprint(payload), 'plan': plan})
        reserved = self.store.reserve(candidates)
        results = []
        for job_id, created in reserved:
            if self.store.claim(job_id):
                row = self.store.get(job_id)
                self._simulate(row)
            result = self.status(job_id)
            result['reused'] = not created
            results.append(result)
        return {'mode': 'dry-run', 'published': False, 'live_ready': False, 'real_authentication_verified': False,
                'provider_requests_sent': 0, 'results': results}

    def _simulate(self, row, reconciliation=False):
        adapter = ADAPTERS[row['platform']]
        try:
            if reconciliation:
                receipt = adapter.confirm(row, self.gateway, row['simulated_ids'])
            else:
                receipt = adapter.simulate(row, self.gateway, lambda ids: self.store.progress(row['id'], ids))
        except (SimulationUncertain, TimeoutError):
            receipt = {'state': 'simulation_unknown', 'error_code': 'confirmation_unknown', 'requires_reconciliation': True,
                       'published': False, 'real_confirmation': False, 'remote_id': None, 'remote_url': None}
        except PublicationError as error:
            receipt = {'state': 'simulation_failed', 'error_code': error.code,
                       'published': False, 'real_confirmation': False, 'remote_id': None, 'remote_url': None}
        except Exception as error:
            # Unknown local failure cannot justify uploading again. Keep IDs
            # and require reconciliation; never serialize raw exception secrets.
            receipt = {'state': 'simulation_unknown', 'error_code': 'unexpected_simulation_error',
                       'error_type': type(error).__name__, 'requires_reconciliation': True,
                       'published': False, 'real_confirmation': False, 'remote_id': None, 'remote_url': None}
        self.store.finish(row['id'], receipt)

    def status(self, job_id):
        row = self.store.get(job_id)
        row['events'] = self.store.events(job_id)
        return row

    def reconcile(self, job_id):
        row = self.store.get(job_id)
        if row['state'] != 'simulation_unknown':
            raise PublicationError('invalid_reconciliation_state', 'Reconciliação somente de simulation_unknown; nenhum upload será repetido')
        if not self.store.claim(job_id, expected='simulation_unknown'):
            return self.status(job_id)
        self._simulate(row, reconciliation=True)
        return self.status(job_id)

    def live(self):
        raise PublicationError('live_disabled', 'Publicação real desabilitada nesta fase; nenhum provedor chamado')

"""Independent publication database. A simulation can never become a real post."""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .models import PublicationError


def now():
    return datetime.now(timezone.utc).isoformat()


class PublicationStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS dry_runs(
                id TEXT PRIMARY KEY, platform TEXT NOT NULL, account TEXT NOT NULL,
                source_video_sha256 TEXT NOT NULL, fingerprint TEXT NOT NULL,
                state TEXT NOT NULL, plan TEXT NOT NULL, receipt TEXT,
                simulated_ids TEXT NOT NULL DEFAULT '{}',
                remote_id TEXT CHECK(remote_id IS NULL), remote_url TEXT CHECK(remote_url IS NULL),
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(platform, account, source_video_sha256));
            CREATE TABLE IF NOT EXISTS dry_run_events(
                seq INTEGER PRIMARY KEY, job_id TEXT NOT NULL, at TEXT NOT NULL,
                state TEXT NOT NULL, detail TEXT NOT NULL);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.root / 'publication.sqlite3', timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def unpack(self, row):
        result = dict(row)
        for field in ['plan', 'receipt', 'simulated_ids']:
            result[field] = json.loads(result[field]) if result[field] else None
        result.update(mode='dry-run', published=False, real_confirmation=False)
        return result

    def reserve(self, candidates):
        # Reserve all platforms atomically: metadata conflict cannot leave a
        # half-created batch, and concurrent requests cannot upload twice.
        ids = []
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            for candidate in candidates:
                existing = db.execute('SELECT * FROM dry_runs WHERE platform=? AND account=? AND source_video_sha256=?',
                                      (candidate['platform'], candidate['account'], candidate['source_video_sha256'])).fetchone()
                if existing:
                    if existing['fingerprint'] != candidate['fingerprint']:
                        raise PublicationError('duplicate_payload_conflict', 'Mesmo vídeo/conta/plataforma já reservado com outro payload; reconcilie antes de alterar')
                    ids.append((existing['id'], False))
                    continue
                job_id = uuid.uuid4().hex
                timestamp = now()
                db.execute('INSERT INTO dry_runs(id,platform,account,source_video_sha256,fingerprint,state,plan,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)',
                           (job_id, candidate['platform'], candidate['account'], candidate['source_video_sha256'],
                            candidate['fingerprint'], 'prepared', json.dumps(candidate['plan'], ensure_ascii=False), timestamp, timestamp))
                db.execute('INSERT INTO dry_run_events(job_id,at,state,detail) VALUES (?,?,?,?)',
                           (job_id, timestamp, 'prepared', 'Plano offline reservado; nenhuma requisição externa'))
                ids.append((job_id, True))
        return ids

    def get(self, job_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM dry_runs WHERE id=?', (job_id,)).fetchone()
        if row is None:
            raise PublicationError('not_found', 'Dry-run inexistente')
        return self.unpack(row)

    def claim(self, job_id, expected='prepared'):
        with self.connect() as db:
            changed = db.execute("UPDATE dry_runs SET state='simulating',updated_at=? WHERE id=? AND state=?", (now(), job_id, expected)).rowcount
            if changed:
                db.execute('INSERT INTO dry_run_events(job_id,at,state,detail) VALUES (?,?,?,?)',
                           (job_id, now(), 'simulating', 'Claim atômico do simulador'))
        return changed == 1

    def progress(self, job_id, ids):
        from .adapters import simulated_id
        for value in ids.values():
            simulated_id(value)
        with self.connect() as db:
            row = db.execute('SELECT simulated_ids FROM dry_runs WHERE id=?', (job_id,)).fetchone()
            combined = json.loads(row[0]) | ids
            db.execute('UPDATE dry_runs SET simulated_ids=?,updated_at=? WHERE id=?', (json.dumps(combined), now(), job_id))
            db.execute('INSERT INTO dry_run_events(job_id,at,state,detail) VALUES (?,?,?,?)',
                       (job_id, now(), 'simulating', json.dumps({'simulated_ids': ids})))

    def finish(self, job_id, receipt):
        if receipt.get('published') is not False or receipt.get('real_confirmation') is not False or receipt.get('remote_id') is not None or receipt.get('remote_url') is not None:
            raise PublicationError('simulation_boundary', 'Simulação não pode declarar publicação real')
        with self.connect() as db:
            db.execute('UPDATE dry_runs SET state=?,receipt=?,updated_at=? WHERE id=?',
                       (receipt['state'], json.dumps(receipt, ensure_ascii=False), now(), job_id))
            db.execute('INSERT INTO dry_run_events(job_id,at,state,detail) VALUES (?,?,?,?)',
                       (job_id, now(), receipt['state'], json.dumps(receipt, ensure_ascii=False)))

    def events(self, job_id):
        self.get(job_id)
        with self.connect() as db:
            return [dict(row) for row in db.execute('SELECT * FROM dry_run_events WHERE job_id=? ORDER BY seq', (job_id,))]

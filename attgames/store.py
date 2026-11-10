import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class Store:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS jobs (
              id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE NOT NULL,
              state TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
              job_id TEXT, at TEXT, state TEXT, message TEXT);
            CREATE TABLE IF NOT EXISTS publications (
              job_id TEXT, platform TEXT, state TEXT, remote_id TEXT, url TEXT,
              UNIQUE(job_id, platform));
            ''')

    @contextmanager
    def db(self):
        with sqlite3.connect(self.root / 'jobs.sqlite3', timeout=30) as db:
            db.row_factory = sqlite3.Row
            yield db

    def create(self, job, fingerprint):
        with self.db() as db:
            cur = db.execute('INSERT OR IGNORE INTO jobs VALUES (?, ?, ?, ?)',
                             (job['id'], fingerprint, job['state'], json.dumps(job)))
            row = db.execute('SELECT payload FROM jobs WHERE fingerprint=?', (fingerprint,)).fetchone()
            return json.loads(row[0]), cur.rowcount == 1

    def get(self, job_id):
        with self.db() as db:
            row = db.execute('SELECT payload FROM jobs WHERE id=?', (job_id,)).fetchone()
        if row is None:
            raise KeyError('Job inexistente')
        job = json.loads(row[0])
        if 'artifacts' in job:
            job['artifacts'] = str(self.root / job['id'])
        return job

    def save(self, job, message):
        with self.db() as db:
            db.execute('UPDATE jobs SET state=?, payload=? WHERE id=?',
                       (job['state'], json.dumps(job, ensure_ascii=False), job['id']))
            db.execute('INSERT INTO events VALUES (?, ?, ?, ?)',
                       (job['id'], datetime.now(timezone.utc).isoformat(), job['state'], message))

    def events(self, job_id):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM events WHERE job_id=? ORDER BY rowid', (job_id,))]

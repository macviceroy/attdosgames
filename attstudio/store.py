import hashlib
import json
import sqlite3
import uuid
from pathlib import Path
from contextlib import closing, contextmanager

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':'))

def uid():
    return uuid.uuid4().hex

class Store:
    def __init__(self, root):
        self.root=Path(root).resolve()
        for directory in ['assets','jobs','incoming']:
            (self.root/directory).mkdir(parents=True,exist_ok=True)
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, revision INTEGER, payload TEXT);
            CREATE TABLE IF NOT EXISTS revisions(id TEXT, revision INTEGER, payload TEXT, PRIMARY KEY(id,revision));
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE, kind TEXT, state TEXT, payload TEXT, result TEXT, error TEXT);
            CREATE TABLE IF NOT EXISTS events(id TEXT, at TEXT DEFAULT CURRENT_TIMESTAMP, message TEXT);
            ''')
    @contextmanager
    def db(self):
        # Connection.__exit__ commits/rolls back but does not close SQLite.
        # Explicit closure also releases the database file on Windows.
        with closing(sqlite3.connect(self.root/'studio.sqlite3', timeout=30)) as db:
            with db:
                db.row_factory=sqlite3.Row
                yield db
    def asset(self, id):
        with self.db() as db:r=db.execute('SELECT payload FROM assets WHERE id=?',(id,)).fetchone()
        if r is None:raise KeyError('Mídia não encontrada')
        return json.loads(r[0])
    def path(self, id):
        a=self.asset(id)
        return self.root/'assets'/id/('source'+a['extension'])
    def add_asset(self,a):
        with self.db() as db:db.execute('INSERT INTO assets VALUES(?,?)',(a['id'],canonical(a)))
    def assets(self):
        with self.db() as db:return [json.loads(r[0]) for r in db.execute('SELECT payload FROM assets ORDER BY rowid DESC')]
    def save(self, project, id=None, revision=None):
        payload=canonical(project)
        with self.db() as db:
            if id is None:
                id=uid(); rev=1
                db.execute('INSERT INTO projects VALUES(?,?,?)',(id,rev,payload))
            else:
                rev=revision+1
                changed=db.execute('UPDATE projects SET revision=?,payload=? WHERE id=? AND revision=?',(rev,payload,id,revision)).rowcount
                if not changed:raise ValueError('Projeto alterado em outra janela. Reabra antes de salvar.')
            db.execute('INSERT INTO revisions VALUES(?,?,?)',(id,rev,payload))
        return self.project(id)
    def project(self,id):
        with self.db() as db:r=db.execute('SELECT * FROM projects WHERE id=?',(id,)).fetchone()
        if r is None:raise KeyError('Projeto não encontrado')
        return {'id':id,'revision':r['revision'],'project':json.loads(r['payload'])}
    def projects(self):
        with self.db() as db:ids=[r[0] for r in db.execute('SELECT id FROM projects ORDER BY rowid DESC')]
        return [self.project(id) for id in ids]
    def history(self,id):
        self.project(id)
        with self.db() as db:return [{'revision':r['revision'],'project':json.loads(r['payload'])} for r in db.execute('SELECT * FROM revisions WHERE id=? ORDER BY revision DESC LIMIT 50',(id,))]
    def enqueue(self,kind,payload):
        fingerprint=hashlib.sha256(canonical([kind,'studio-0.3.1',payload]).encode()).hexdigest()
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute('SELECT id FROM jobs WHERE fingerprint=?',(fingerprint,)).fetchone()
            if existing:return self.job(existing[0]),False
            if db.execute("SELECT count(*) FROM jobs WHERE state IN ('queued','running')").fetchone()[0]>=8:
                raise ValueError('Fila cheia: aguarde ou cancele um trabalho')
            id=uid()
            db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?)',(id,fingerprint,kind,'queued',canonical(payload),None,None))
            db.execute('INSERT INTO events(id,message) VALUES(?,?)',(id,'Na fila'))
        return self.job(id),True
    def job(self,id):
        with self.db() as db:r=db.execute('SELECT * FROM jobs WHERE id=?',(id,)).fetchone()
        if r is None:raise KeyError('Trabalho não encontrado')
        d=dict(r);d['payload']=json.loads(d['payload']);d['result']=json.loads(d['result']) if d['result'] else None
        return d
    def jobs(self):
        with self.db() as db:ids=[r[0] for r in db.execute('SELECT id FROM jobs ORDER BY rowid DESC LIMIT 100')]
        return [self.job(id) for id in ids]
    def state(self,id,state,result=None,error=None):
        with self.db() as db:
            db.execute('UPDATE jobs SET state=?,result=?,error=? WHERE id=?',(state,canonical(result) if result is not None else None,error,id))
            db.execute('INSERT INTO events(id,message) VALUES(?,?)',(id,state + (': '+error if error else '')))
    def events(self,id):
        with self.db() as db:return [dict(r) for r in db.execute('SELECT at,message FROM events WHERE id=? ORDER BY rowid',(id,))]

"""Signed, expiring delivery capabilities; no social provider or publication calls."""
import argparse
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time
import tempfile
from urllib.parse import urlencode, urlsplit
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from .media import prepare, sha256
from .models import Submission, PublicationError

FILES = {'video': ('video.mp4','video/mp4'), 'cover': ('cover.png','image/png'),
         'instagram_cover': ('cover-instagram.jpg','image/jpeg')}


class Handoff:
    def __init__(self, root=None, clock=time.time):
        self.root=Path(root or os.environ.get('ATT_HANDOFF_DATA_DIR','handoff-data')).resolve()
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.clock=clock
        keyfile=self.root/'signing.key'
        os.chmod(self.root,0o700)
        if not keyfile.exists():
            fd,temporary=tempfile.mkstemp(dir=self.root,prefix='.key-')
            try:
                with os.fdopen(fd,'wb') as stream:
                    stream.write(secrets.token_bytes(32))
                try: os.link(temporary,keyfile)
                except FileExistsError: pass
            finally: os.unlink(temporary)
        os.chmod(keyfile,0o600)
        self.key=keyfile.read_bytes()
        if len(self.key)!=32: raise ValueError('Invalid signing key; retry after initialization')
        with self.db() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS handoffs(
                id TEXT PRIMARY KEY, fingerprint TEXT UNIQUE, nonce TEXT, expires INTEGER,
                revoked INTEGER, origin TEXT, assets TEXT, metadata TEXT)''')
        os.chmod(self.root/'handoffs.sqlite3',0o600)

    @contextmanager
    def db(self):
        db=sqlite3.connect(self.root/'handoffs.sqlite3',timeout=30)
        db.row_factory=sqlite3.Row
        try:
            with db: yield db
        finally: db.close()

    def row(self, identifier):
        with self.db() as db: row=db.execute('SELECT * FROM handoffs WHERE id=?',(identifier,)).fetchone()
        if row is None: raise PublicationError('not_found','Entrega não encontrada')
        return dict(row)

    def signature(self,row,resource):
        value=json.dumps([row['id'],row['nonce'],row['expires'],resource],separators=(',',':'))
        return hmac.new(self.key,value.encode(),hashlib.sha256).hexdigest()

    def url(self,row,resource):
        return row['origin']+'/handoffs/'+row['id']+'/'+resource+'?'+urlencode({'expires':row['expires'],'signature':self.signature(row,resource)})

    def issue(self,submission,origin,ttl=900,renew=False):
        parsed=urlsplit(origin)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
            raise PublicationError('invalid_origin','Configure uma origem HTTPS, sem caminho, credenciais ou query')
        if not 60<=ttl<=3600: raise PublicationError('invalid_ttl','TTL deve ser de 60 a 3600 segundos')
        origin=origin.rstrip('/')
        assets=prepare(submission.video,submission.cover,self.root)
        metadata={'title':submission.title,'description':submission.description,'hashtags':submission.hashtags,
                  'platforms':submission.platforms,'made_for_kids':submission.made_for_kids,
                  'mode':'dry-run','publication_allowed':False,'rights_and_editorial_approval':'pending'}
        fingerprint=hashlib.sha256(json.dumps([assets['hashes'],metadata,origin],sort_keys=True).encode()).hexdigest()
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            old=db.execute('SELECT * FROM handoffs WHERE fingerprint=?',(fingerprint,)).fetchone()
            if old:
                identifier=old['id']
                if renew:
                    db.execute('UPDATE handoffs SET nonce=?,expires=?,revoked=0 WHERE id=?',
                               (secrets.token_hex(16),int(self.clock())+ttl,identifier))
                elif old['revoked'] or old['expires']<=self.clock():
                    raise PublicationError('renew_required','Entrega expirada/revogada; renovação explícita necessária')
            else:
                identifier=secrets.token_hex(16)
                db.execute('INSERT INTO handoffs VALUES(?,?,?,?,?,?,?,?)',
                           (identifier,fingerprint,secrets.token_hex(16),int(self.clock())+ttl,0,origin,json.dumps(assets),json.dumps(metadata)))
        row=self.row(identifier)
        return {'id':identifier,'expires_at_unix':row['expires'],'manifest_url':self.url(row,'manifest'),
                'mode':'dry-run','publication_allowed':False,'hosting_verified':False}

    def authorize(self,identifier,resource,expires,signature):
        row=self.row(identifier)
        if row['revoked'] or row['expires']<=self.clock(): raise PublicationError('gone','Entrega expirada ou revogada')
        if expires!=row['expires'] or not hmac.compare_digest(self.signature(row,resource).encode(),signature.encode()):
            raise PublicationError('forbidden','Assinatura inválida')
        return row

    def manifest(self,row):
        assets=json.loads(row['assets'])
        return {**json.loads(row['metadata']),'id':row['id'],'expires_at_unix':row['expires'],
                'files':{name:{'url':self.url(row,name),'sha256':assets['hashes'][filename],'mime_type':mime}
                         for name,(filename,mime) in FILES.items()},
                'delivery_confirmation_is_not_publication':True}

    def revoke(self,identifier):
        self.row(identifier)
        with self.db() as db: db.execute('UPDATE handoffs SET revoked=1 WHERE id=?',(identifier,))
        return {'id':identifier,'revoked':True}


app=FastAPI(title='ATT delivery only — no publishing')


@app.middleware('http')
async def private_responses(request:Request,call_next):
    response=await call_next(request)
    response.headers['Cache-Control']='no-store, private'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Content-Type-Options']='nosniff'
    return response


@app.exception_handler(PublicationError)
async def failed(request,error):
    status={'not_found':404,'gone':410,'forbidden':403}.get(error.code,409)
    return JSONResponse({'error':error.code},status_code=status)


@app.get('/handoffs/{identifier}/{resource}')
def consume(identifier:str,resource:str,expires:int,signature:str):
    if resource not in {'manifest',*FILES}: raise HTTPException(404)
    delivery=Handoff()
    row=delivery.authorize(identifier,resource,expires,signature)
    if resource=='manifest': return delivery.manifest(row)
    assets=json.loads(row['assets']);filename,mime=FILES[resource]
    path=Path(assets['directory'])/filename
    if not path.is_file() or sha256(path)!=assets['hashes'][filename]:
        raise HTTPException(409,detail='asset_integrity')
    return FileResponse(path,media_type=mime,filename=filename)


def main():
    parser=argparse.ArgumentParser(description='Entrega temporária, nunca publicação')
    sub=parser.add_subparsers(dest='command',required=True)
    create=sub.add_parser('create');create.add_argument('--manifest',type=Path,required=True)
    create.add_argument('--origin',required=True);create.add_argument('--ttl',type=int,default=900)
    create.add_argument('--renew',action='store_true')
    revoke=sub.add_parser('revoke');revoke.add_argument('--id',required=True)
    args=parser.parse_args()
    try:
        delivery=Handoff()
        if args.command=='revoke':result=delivery.revoke(args.id)
        else:
            submission=Submission.model_validate_json(args.manifest.read_text())
            result=delivery.issue(submission,args.origin,args.ttl,args.renew)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception:
        # Never echo URLs, signatures, credential input or raw validation data.
        print(json.dumps({'error':'handoff_failed','detail':'Verifique manifesto, arquivos, origem HTTPS e TTL; nenhuma publicação executada'}))
        raise SystemExit(2)


if __name__=='__main__':main()

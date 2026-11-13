import json
import os
import re
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from filelock import FileLock
from pydantic import ValidationError
from .models import Project, Save, Analyze, Transcribe, Command
from .store import Store, uid
from .media import inspect_upload, ff, input_args, digest, validate_project, amf_available
from .jobs import Queue

STATIC=Path(__file__).parent/'static'
EXPORTS={'video.mp4','cover.png','cover.jpg','captions.srt','script.txt','metadata.json','report.json','project.json'}

def create_app(root=None):
    db=Store(root or os.environ.get('ATT_STUDIO_DIR','studio-data'))
    queue=Queue(db)
    @asynccontextmanager
    async def lifespan(app):
        # Only one server owns recovery/queue. Works on Windows and Unix.
        lock=FileLock(str(db.root/'server.lock'),timeout=0)
        with lock:
            queue.recover()
            yield
            await run_in_threadpool(queue.close)
    app=FastAPI(title='ATT DOS GAMES Studio',lifespan=lifespan)
    app.state.db=db;app.state.queue=queue
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','[::1]','testserver'])
    @app.middleware('http')
    async def local_only(request,call_next):
        if request.client and request.client.host not in {'127.0.0.1','::1','testclient'}:
            return JSONResponse({'detail':'Servidor exclusivo para loopback'},403)
        if request.method not in {'GET','HEAD','OPTIONS'}:
            if request.headers.get('x-att-studio')!='1':return JSONResponse({'detail':'Cabeçalho X-ATT-Studio obrigatório'},403)
            origin=request.headers.get('origin')
            if origin and origin!=str(request.base_url).rstrip('/'):
                return JSONResponse({'detail':'Origem não autorizada'},403)
        response=await call_next(request)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; media-src 'self' blob:; img-src 'self' blob: data:; frame-ancestors 'none'; connect-src 'self'"
        response.headers['Referrer-Policy']='no-referrer'
        return response
    @app.exception_handler(KeyError)
    async def missing(request,e):return JSONResponse({'detail':str(e)},404)
    @app.exception_handler(RuntimeError)
    async def processing_error(request,e):return JSONResponse({'detail':str(e)},422)
    @app.exception_handler(ValueError)
    async def invalid(request,e):return JSONResponse({'detail':str(e)},409)
    @app.get('/')
    def home():return FileResponse(STATIC/'index.html')
    app.mount('/static',StaticFiles(directory=STATIC),name='static')
    @app.get('/api/capabilities')
    def capabilities():
        from .fonts import available
        return {'fonts':available(),'voice':{'name':'ATT DOS GAMES - Brasileiro Alex','connected':False,'input':'WAV/MP3 importado'},
                'transcription_configured':bool(os.environ.get('ATT_WHISPER_MODEL')),
                'publication':False,'analysis':'cenas, atividade visual e áudio; sem semântica','encoder_default':'cpu'}
    @app.post('/api/check-amd')
    def check_amd():return {'available':amf_available()}
    @app.post('/api/music/{style}')
    def original_music(style:str):
        from .audio import generate
        return generate(db,style)
    @app.get('/api/assets')
    def assets():return db.assets()
    @app.post('/api/assets')
    async def upload(request:Request,filename:str=Query(max_length=180),kind:str=Query(pattern='^(video|audio|image)$'),rights:str=Query(min_length=5,max_length=500)):
        extensions={'video':{'.mp4','.mov','.mkv','.webm','.avi'},'audio':{'.wav','.mp3','.flac','.ogg'},'image':{'.png','.jpg','.jpeg'}}
        ext=Path(filename).suffix.lower()
        if ext not in extensions[kind]:raise HTTPException(415,'Extensão não permitida')
        id=uid();temp=db.root/'incoming'/id;limit=512*1024*1024;size=0
        try:
            with temp.open('xb') as stream:
                async for chunk in request.stream():
                    size+=len(chunk)
                    if size>limit:raise HTTPException(413,'Máximo 512 MiB por arquivo')
                    stream.write(chunk)
            if not size:raise ValueError('Arquivo vazio')
            def finish():
                info=inspect_upload(temp,kind);folder=db.root/'assets'/id;folder.mkdir()
                dest=folder/('source'+ext)
                try:
                    shutil.move(str(temp),dest)
                    if kind=='video':ff([*input_args(dest),'-frames:v','1','-vf','scale=320:-2',str(folder/'thumbnail.jpg')],timeout=60)
                    if kind=='image':
                        from PIL import Image,ImageOps
                        with Image.open(dest) as image:ImageOps.exif_transpose(image).convert('RGB').resize((180,320)).save(folder/'thumbnail.jpg')
                    a={'id':id,'name':Path(filename.replace('\\','/')).name,'extension':ext,'kind':kind,'bytes':size,'rights':rights,'sha256':digest(dest),**info}
                    db.add_asset(a);return a
                except BaseException:shutil.rmtree(folder,ignore_errors=True);raise
            return await run_in_threadpool(finish)
        finally:temp.unlink(missing_ok=True)
    @app.get('/api/assets/{id}/file')
    def asset_file(id:str):return FileResponse(db.path(id))
    @app.get('/api/assets/{id}/thumbnail')
    def thumbnail(id:str):
        db.asset(id);path=db.root/'assets'/id/'thumbnail.jpg'
        if not path.exists():raise HTTPException(404,'Sem miniatura')
        return FileResponse(path)
    @app.get('/api/projects')
    def projects():return db.projects()
    @app.post('/api/projects')
    def create(project:Project):
        validate_project(db,project);return db.save(project.model_dump())
    @app.get('/api/projects/{id}')
    def project(id:str):return db.project(id)
    @app.put('/api/projects/{id}')
    def save(id:str,body:Save):
        validate_project(db,body.project);return db.save(body.project.model_dump(),id,body.revision)
    @app.get('/api/projects/{id}/history')
    def history(id:str):return db.history(id)
    @app.post('/api/projects/{id}/render')
    def render(id:str):
        p=db.project(id);validate_project(db,Project.model_validate(p['project']))
        # Fingerprint omits revision: undoing to identical settings reuses the same output.
        return queue.submit('render',{'project_id':id,'project':p['project']})
    @app.post('/api/projects/{id}/command')
    def command(id:str,body:Command):
        from .commands import propose
        return propose(Project.model_validate(db.project(id)['project']),body.text)
    @app.post('/api/analyze')
    def analyze(body:Analyze):
        if db.asset(body.asset)['kind']!='video':raise ValueError('Selecione um vídeo')
        return queue.submit('analyze',body.model_dump())
    @app.post('/api/transcribe')
    def transcribe(body:Transcribe):
        db.asset(body.asset)
        if not os.environ.get('ATT_WHISPER_MODEL'):raise ValueError('Modelo local não configurado; importe SRT ou configure ATT_WHISPER_MODEL')
        return queue.submit('transcribe',body.model_dump())
    @app.get('/api/jobs')
    def jobs():return db.jobs()
    @app.get('/api/jobs/{id}')
    def job(id:str):return {**db.job(id),'events':db.events(id)}
    @app.post('/api/jobs/{id}/cancel')
    def cancel(id:str):return queue.cancel(id)
    @app.post('/api/jobs/{id}/retry')
    def retry(id:str):return queue.retry(id)
    @app.get('/api/jobs/{id}/files/{name}')
    def artifact(id:str,name:str):
        job=db.job(id)
        if job['state'] not in {'completed','qc_failed'}:raise HTTPException(409,'Artefato ainda não disponível')
        if name not in EXPORTS and not re.fullmatch(r'moment-[0-5]\.jpg',name):raise HTTPException(404,'Artefato inválido')
        path=db.root/'jobs'/id/name
        if not path.is_file():raise HTTPException(404,'Artefato ausente')
        expected=(job['result'] or {}).get('hashes',{}).get(name)
        if expected and digest(path)!=expected:raise HTTPException(409,'Integridade do artefato inválida')
        return FileResponse(path)
    @app.post('/api/publish')
    def publish():raise HTTPException(423,'Publicação desativada. Nenhum conteúdo enviado.')
    return app

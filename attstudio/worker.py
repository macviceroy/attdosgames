import json
import shutil
import sys
from .store import Store
from .media import Cancelled

def execute(root,id):
    from filelock import FileLock
    db=Store(root)
    with FileLock(str(db.root/'jobs'/(id+'.lock')),timeout=0):
        _execute(root,id)

def _execute(root,id):
    db=Store(root);job=db.job(id);folder=db.root/'jobs'/id;folder.mkdir(exist_ok=True);cancel=folder/'cancel'
    with db.db() as con:
        claimed=con.execute("UPDATE jobs SET state='running' WHERE id=? AND state='queued'",(id,)).rowcount
    if not claimed:return
    try:
        if cancel.exists():raise Cancelled('Cancelado antes de iniciar')
        if job['kind']=='render':
            from .render import render
            result=render(db,job['payload'],folder,cancel)
        elif job['kind']=='cover':
            from .covers import generate
            result=generate(db,job['payload'],folder,cancel)
        elif job['kind']=='analyze':
            from .analysis import analyze
            result=analyze(db,job['payload'],folder,cancel)
        elif job['kind']=='transcribe':
            from .transcription import transcribe
            result=transcribe(db,job['payload'],folder,cancel)
        elif job['kind']=='import_url':
            from .importers import download
            result=download(db,job['payload'],folder,cancel)
        else:raise ValueError('Tipo de trabalho inválido')
        if cancel.exists():raise Cancelled('Cancelado')
        state='completed' if job['kind']!='render' or result['quality']['technical_pass'] else 'qc_failed'
        db.state(id,state,result)
    except Cancelled as e:
        db.state(id,'cancelled',error=str(e))
    except Exception as e:
        db.state(id,'failed',error=str(e));raise
    finally:
        shutil.rmtree(folder/'temp',ignore_errors=True)
        if db.job(id)['state'] in {'cancelled','failed'}:
            for path in folder.iterdir():
                if path.is_file() and path.name not in {'worker.log','cancel'}:path.unlink(missing_ok=True)

if __name__=='__main__':execute(*sys.argv[1:])

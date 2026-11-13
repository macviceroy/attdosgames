import os
import subprocess
import sys
import threading
import time
import signal
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .media import run
from filelock import FileLock, Timeout

class Queue:
    def __init__(self,db):
        self.db=db;self.pool=ThreadPoolExecutor(max_workers=2);self.active=set();self.lock=threading.Lock()
    def recover(self):
        # Called only while holding the app's exclusive cross-platform FileLock.
        for job in self.db.jobs():
            if job['state'] in {'queued','running','cancelling'}:
                try:
                    with FileLock(str(self.db.root/'jobs'/(job['id']+'.lock')),timeout=0):
                        self.db.state(job['id'],'interrupted',error='Servidor anterior interrompido. Revise e use Retentar.')
                except Timeout:
                    # A surviving worker still owns its output directory. Keep observing it.
                    pass
    def submit(self,kind,payload):
        job,created=self.db.enqueue(kind,payload)
        if created:self.launch(job['id'])
        return job
    def launch(self,id):
        with self.lock:
            if id in self.active:return
            self.active.add(id)
        self.pool.submit(self.execute,id)
    def execute(self,id):
        try:
            folder=self.db.root/'jobs'/id;folder.mkdir(exist_ok=True)
            log=folder/'worker.log'
            with log.open('w',encoding='utf-8') as out:
                options = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name=='nt' else {'start_new_session':True}
                proc=subprocess.Popen([sys.executable,'-m','attstudio.worker',str(self.db.root),id],stdout=out,stderr=out,**options)
                deadline=time.monotonic()+3600
                cancel_since=None
                while proc.poll() is None:
                    if time.monotonic()>deadline:(folder/'cancel').touch()
                    if (folder/'cancel').exists():
                        if cancel_since is None:cancel_since=time.monotonic()
                        if time.monotonic()-cancel_since>15:
                            # Kill this worker's tree only if cooperative cancellation stalls.
                            if os.name=='nt':subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True,timeout=20)
                            else:
                                try:os.killpg(proc.pid,signal.SIGKILL)
                                except ProcessLookupError:pass
                            proc.wait(timeout=20)
                            self.db.state(id,'cancelled',error='Árvore do worker encerrada após cancelamento')
                            break
                    time.sleep(.2)
            if proc.returncode and self.db.job(id)['state'] not in {'failed','cancelled'}:
                self.db.state(id,'failed',error='Worker encerrou; consulte o log local')
        except Exception as e:self.db.state(id,'failed',error=str(e))
        finally:
            with self.lock:self.active.discard(id)
    def cancel(self,id):
        job=self.db.job(id)
        if job['state'] not in {'queued','running','cancelling'}:return job
        folder=self.db.root/'jobs'/id;folder.mkdir(exist_ok=True);(folder/'cancel').touch()
        # State is finalized by worker, not marked terminal while FFmpeg is alive.
        return self.db.job(id)
    def retry(self,id):
        with self.lock:
            if id in self.active:raise ValueError('Worker ainda ativo')
            job=self.db.job(id)
            if job['state'] not in {'failed','cancelled','interrupted','qc_failed'}:raise ValueError('Trabalho não pode ser retomado')
            import shutil
            try:
                with FileLock(str(self.db.root/'jobs'/(id+'.lock')),timeout=0):
                    folder=self.db.root/'jobs'/id
                    if folder.exists():shutil.rmtree(folder)
                    self.db.state(id,'queued')
            except Timeout as exc:
                raise ValueError('Worker anterior ainda possui os arquivos; aguarde ou cancele') from exc
        self.launch(id);return self.db.job(id)
    def close(self):
        for job in self.db.jobs():
            if job['state'] in {'queued','running'}:self.cancel(job['id'])
        self.pool.shutdown(wait=True)

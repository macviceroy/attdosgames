import hashlib
import json
import os
import signal
import subprocess
import sys
import uuid
from pathlib import Path
from .store import Store
from .editor import render, digest
from .quality import inspect


def store():
    return Store(Path(os.environ.get('ATT_DATA_DIR', 'data')))


def validate(theme, duration):
    theme = ' '.join(theme.split())
    if not 1 <= len(theme) <= 64:
        raise ValueError('Tema deve ter de 1 a 64 caracteres')
    if not 10 <= duration <= 60:
        raise ValueError('Duração deve estar entre 10 e 60 segundos')
    return theme


def run_worker(job_id):
    # Kill the complete process group on timeout: no orphan FFmpeg may keep
    # writing into a job that becomes eligible for retry.
    process = subprocess.Popen([sys.executable, '-m', 'attgames.worker', job_id],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=1800)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)


def produce(theme, duration=35, retry=False):
    theme = validate(theme, duration)
    db = store()
    fingerprint = hashlib.sha256(json.dumps(['phase1-v1', theme, duration]).encode()).hexdigest()
    job, created = db.create({'id': uuid.uuid4().hex, 'theme': theme, 'duration': duration,
                              'state': 'queued', 'phase': 1}, fingerprint)
    if not created:
        if not retry or job['state'] not in {'failed', 'qc_failed'}:
            return job
        attempts = job.get('attempts', 1)
        if attempts >= 3:
            raise ValueError('Limite de 3 tentativas atingido; investigue os logs')
        job.update(state='queued', attempts=attempts + 1)
        with db.db() as connection:
            changed = connection.execute(
                "UPDATE jobs SET state='queued', payload=? WHERE id=? AND state IN ('failed','qc_failed')",
                (json.dumps(job), job['id'])).rowcount
        if not changed:
            return db.get(job['id'])

    db.save(job, 'Job criado; chave idempotente por tema/duração/versão')
    # Separate process: eSpeak uses process-global state, never share across API threads.
    try:
        result = run_worker(job['id'])
        if result.returncode:
            raise RuntimeError(result.stderr[-3000:])
    except (subprocess.SubprocessError, RuntimeError) as exc:
        job = db.get(job['id'])
        job.update(state='failed', error=str(exc))
        db.save(job, 'Worker falhou; nenhuma publicação executada')
    return db.get(job['id'])


def execute(job_id):
    db = store()
    job = db.get(job_id)
    # Atomic claim protects accidental duplicate workers.
    with db.db() as connection:
        claimed = connection.execute("UPDATE jobs SET state='rendering' WHERE id=? AND state='queued'", (job_id,)).rowcount
    if not claimed:
        return
    job['state'] = 'rendering'
    db.save(job, 'Renderização iniciada')
    folder = db.root / job_id
    if folder.exists() and job.get('attempts', 1) > 1:
        import shutil
        previous = db.root / (job_id + '-attempt-' + str(job['attempts'] - 1))
        if previous.exists():
            raise RuntimeError('Backup de tentativa já existe; reconciliação necessária')
        shutil.move(str(folder), str(previous))
    folder.mkdir(exist_ok=True)
    try:
        scenes, assets, voice = render(folder, job['theme'], job['duration'])
        (folder / 'titulo.txt').write_text(f"GTA VI: {job['theme']} | DEMONSTRAÇÃO ATT DOS GAMES\n")
        (folder / 'legenda.txt').write_text('DEMONSTRAÇÃO TÉCNICA — sem notícias verificadas. Arte original, sem imagens do jogo. @attdosgames\n#ATTDOSGAMES #GTAVI #GTA6 #Games\n')
        report = {'schema_version': 1, 'phase': 1, 'demo': True, 'job_id': job_id,
                  'sources': [], 'research_status': 'not_connected_no_factual_news_claims',
                  'assets': assets, 'voice': voice, 'music': None,
                  'artwork_license': 'CC0-1.0: arte procedural original dedicada ao domínio público',
                  'font_license': 'DejaVu/Bitstream Vera — brand/DejaVu-LICENSE.txt; custom fonts: respective sidecar',
                  'subtitle_precision': 'phrase-level; each utterance fitted into its caption interval',
                  'hashes': {p.name: digest(p) for p in folder.iterdir() if p.is_file()}}
        (folder / 'relatorio.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
        qc = inspect(folder, job['duration'])
        (folder / 'qualidade.json').write_text(json.dumps(qc, ensure_ascii=False, indent=2))
        job.update(state='review_required' if qc['technical_pass'] else 'qc_failed',
                   artifacts=str(folder), quality=qc)
        db.save(job, 'Renderização concluída; revisão obrigatória')
    except Exception as exc:
        job.update(state='failed', error=str(exc))
        db.save(job, 'Falha de produção; ver erro no job')
        raise


def review(job_id):
    db = store()
    job = db.get(job_id)
    if 'artifacts' not in job:
        raise ValueError('Job ainda não possui artefatos revisáveis')
    qc = inspect(Path(job['artifacts']), job['duration'])
    job.update(quality=qc, state='review_required' if qc['technical_pass'] else 'qc_failed')
    (Path(job['artifacts']) / 'qualidade.json').write_text(json.dumps(qc, ensure_ascii=False, indent=2))
    db.save(job, 'QC reexecutado; revisão não concede autorização de publicação')
    return job


def publish(job_id, platforms):
    platforms = set(platforms.split(','))
    if not platforms or not platforms <= {'instagram', 'youtube'}:
        raise ValueError('Plataformas válidas: instagram,youtube')
    db = store()
    job = db.get(job_id)
    db.save(job, 'Publicação bloqueada: adaptadores não implementados na Fase 1')
    raise ValueError('Publicação indisponível na Fase 1; nenhum pedido enviado às plataformas')

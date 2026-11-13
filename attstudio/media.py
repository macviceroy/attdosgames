"""Trusted executable names, bounded commands, local protocols only."""
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path
from PIL import Image

class Cancelled(RuntimeError):pass

def digest(path):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def run(args, cwd=None, cancel=None, timeout=1800):
    # Files avoid PIPE deadlock and unbounded RAM for FFmpeg diagnostics.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc=subprocess.Popen([str(a) for a in args],cwd=cwd,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
        start=time.monotonic()
        try:
            while proc.poll() is None:
                if cancel and cancel.exists():raise Cancelled('Cancelado pelo usuário')
                if time.monotonic()-start>timeout:raise TimeoutError('Tempo máximo do processo excedido')
                time.sleep(.1)
        except BaseException:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            raise
        err.seek(0,2);err.seek(max(0,err.tell()-4000));error=err.read().decode('utf-8',errors='replace')
        if proc.returncode:raise RuntimeError(error)
        out.seek(0);return out.read().decode('utf-8',errors='replace')

def ff(args,**kwargs):
    return run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-filter_complex_threads','1',*args],**kwargs)

def input_args(path):
    return ['-protocol_whitelist','file,pipe','-i',str(path)]

def probe(path):
    return json.loads(run(['ffprobe','-v','error','-protocol_whitelist','file,pipe','-show_format','-show_streams','-of','json',path],timeout=30))

def inspect_upload(path,kind):
    if kind=='image':
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            if im.width*im.height>25000000:raise ValueError('Imagem maior que 25 megapixels')
            return {'width':im.width,'height':im.height,'duration':0,'audio':False}
    m=probe(path);streams=m['streams'];video=next((s for s in streams if s['codec_type']=='video' and not s.get('disposition',{}).get('attached_pic')),None)
    audio=any(s['codec_type']=='audio' for s in streams)
    formats=set(m['format']['format_name'].split(','))
    if not formats.intersection({'mov','mp4','matroska','webm','avi','wav','mp3','flac','ogg'}):raise ValueError('Contêiner não permitido')
    duration=float(m['format'].get('duration',0))
    if not .2<=duration<=14400:raise ValueError('Duração inválida (máximo 4 horas)')
    if kind=='video' and not video:raise ValueError('Nenhuma trilha de vídeo')
    if kind=='audio' and not audio:raise ValueError('Nenhuma trilha de áudio')
    if video and (video['width']*video['height']>34000000 or min(video['width'],video['height'])<16):raise ValueError('Resolução fora do limite')
    return {'duration':duration,'width':video['width'] if video else 0,'height':video['height'] if video else 0,'audio':audio,'format':m['format']['format_name']}

def validate_project(db,p):
    from .fonts import path
    path(p.captions.font);path(p.cover.font)
    for layer in p.text_layers:path(layer.font)
    for c in p.clips:
        a=db.asset(c.asset)
        if a['kind']!='video' or c.end>a['duration']+.03:raise ValueError('Trecho fora da mídia de vídeo')
    for track in [p.narration,p.music]:
        if track:
            a=db.asset(track.asset)
            if not a['audio'] or a['kind'] not in {'audio','video'}:raise ValueError('Trilha sem áudio')
            if track.offset>=p.duration:raise ValueError('Trilha fora da linha do tempo')
    if p.narration and db.asset(p.narration.asset)['duration']+p.narration.offset>p.duration+.1:
        raise ValueError('Narração seria cortada: aumente a duração ou importe um áudio menor')
    if p.cover.image and db.asset(p.cover.image)['kind']!='image':raise ValueError('Base da capa deve ser imagem')
    ids={c.asset for c in p.clips}|{t.asset for t in [p.narration,p.music] if t}
    if p.cover.image:ids.add(p.cover.image)
    for id in ids:
        a=db.asset(id)
        if not a.get('rights'):raise ValueError('Confirmação de direitos ausente')
        if not db.path(id).is_file() or digest(db.path(id))!=a['sha256']:raise ValueError('Integridade da entrada inválida')
    return [db.asset(id) for id in sorted(ids)]

def amf_available():
    try:
        ff(['-f','lavfi','-i','color=s=1080x1920:r=30:d=0.1','-an','-c:v','h264_amf','-f','null','-'],timeout=20)
        return True
    except (RuntimeError,OSError,TimeoutError):return False

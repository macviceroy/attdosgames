"""Explicit optional local model. No implicit downloads or cloud calls."""
import os
from pathlib import Path
from .media import Cancelled

def configured_model():
    configured=os.environ.get('ATT_WHISPER_MODEL')
    if configured:return Path(configured)
    from .runtime import default_data_dir
    local=default_data_dir()/'models'/'faster-whisper-small'
    return local if local.is_dir() else None

def transcribe(db,payload,folder,cancel):
    model_path=configured_model()
    if not model_path or not model_path.is_dir():
        raise ValueError('Configure ATT_WHISPER_MODEL com um modelo faster-whisper local; nenhum download é automático')
    if not db.asset(payload['asset'])['audio']:raise ValueError('Mídia sem áudio')
    import onnxruntime
    onnxruntime.disable_telemetry_events()
    from faster_whisper import WhisperModel
    model=WhisperModel(str(model_path),device='cpu',compute_type='int8',cpu_threads=2,local_files_only=True)
    segments,info=model.transcribe(str(db.path(payload['asset'])),language='pt',word_timestamps=True,vad_filter=True)
    words=[]
    for segment in segments:
        if cancel.exists():raise Cancelled('Transcrição cancelada')
        for word in segment.words or []:
            if word.end>word.start:
                words.append({'start':round(word.start,3),'end':round(word.end,3),'text':word.word.strip()})
    return {'language':'pt','locale_requested':'pt-BR','locale_verified':False,'cues':words,
            'script':' '.join(w['text'] for w in words),'model':Path(model_path).name,
            'review_required':True,'note':'Whisper distingue português, não comprova variante brasileira. Revise palavras e tempos.'}

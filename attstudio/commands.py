"""Small deterministic grammar: proposals only, no eval/LLM/shell."""
import re
from .models import Project

def propose(project,text):
    p=project.model_dump();s=text.lower().strip().rstrip('.')
    if s in ['deixe a música mais baixa','abaixe a música']:
        if not p['music']:raise ValueError('Adicione música primeiro')
        p['music']['volume']=round(p['music']['volume']*.5,3)
    elif s in ['troque as legendas pelo estilo neon','legendas neon']:
        p['captions']['style']='neon'
    elif re.fullmatch(r'corte os primeiros (\d+(?:[.,]\d+)?) segundos',s):
        seconds=float(re.search(r'\d+(?:[.,]\d+)?',s)[0].replace(',','.'))
        if seconds>=project.duration-.5:raise ValueError('Corte removeria todo o vídeo')
        remaining=seconds;clips=[]
        for c in p['clips']:
            length=c['end']-c['start']
            if remaining>=length:remaining-=length;continue
            c['start']+=remaining;remaining=0;clips.append(c)
        p['clips']=clips
        if p['narration'] or p['captions']['cues']:raise ValueError('Ajuste a narração e as legendas antes de cortar por comando')
        p['cover']['time']=0
    else:raise ValueError('Comandos disponíveis: corte os primeiros N segundos; deixe a música mais baixa; legendas Neon')
    checked=Project.model_validate(p)
    return {'proposal':checked.model_dump(),'applied':False,'message':'Revise a proposta; salvar cria uma nova revisão sem alterar a mídia original.'}

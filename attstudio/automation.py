"""Deterministic helpers based on user-owned media; no invented facts or cloud LLM."""
import re


def script_from_transcript(title: str, transcript: str) -> dict:
    clean=' '.join(transcript.split())
    sentences=[x.strip() for x in re.split(r'(?<=[.!?])\s+',clean) if x.strip()]
    if not sentences:
        raise ValueError('A transcrição não contém fala utilizável')
    hook=sentences[0]
    if len(hook)>105:
        hook=hook[:102].rsplit(' ',1)[0]+'…'
    selected=[];count=0
    for sentence in sentences[1:] or sentences:
        if count+len(sentence)>520:break
        selected.append(sentence);count+=len(sentence)
    body=' '.join(selected) or clean[:520]
    script=(f'{hook}\n\n{body}\n\nO que você achou? Conta para o ATT DOS GAMES.').strip()
    return {'script':script,'hook':hook,'title':title,
            'description':f'{title}. Trecho editado a partir do vídeo enviado pelo usuário.',
            'hashtags':['#ATTDOSGAMES','#Games','#Shorts'],
            'source':'transcrição do vídeo; resumo determinístico sem pesquisa factual',
            'review_required':True}

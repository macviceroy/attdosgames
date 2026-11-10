"""API local. Não expor publicamente sem autenticação e limites de jobs."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .pipeline import produce, review, publish, store

app = FastAPI(title='ATT DOS GAMES', version='0.1.0')

class Production(BaseModel):
    tema: str = Field(min_length=1, max_length=64)
    duracao: int = Field(default=35, ge=10, le=60)
    retomar: bool = False

class Publication(BaseModel):
    plataformas: str = 'instagram,youtube'


def invoke(function, *args):
    try:
        return function(*args)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.post('/produzir')
def production(body: Production):
    return invoke(produce, body.tema, body.duracao, body.retomar)

@app.get('/status/{job_id}')
def status(job_id: str):
    return invoke(store().get, job_id)

@app.post('/revisar/{job_id}')
def revision(job_id: str):
    return invoke(review, job_id)

@app.post('/publicar/{job_id}')
def publication(job_id: str, body: Publication):
    return invoke(publish, job_id, body.plataformas)

"""Local offline API. Remote access requires a secret key; no provider transport."""
import os
import secrets
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .models import PublicationError, Submission
from .service import PublicationService

app = FastAPI(title='ATT DOS GAMES — Publication dry-run', version='0.2.0')


@app.middleware('http')
async def inbound_auth(request: Request, call_next):
    key = os.environ.get('ATT_PUBLISH_API_KEY')
    local = request.client and request.client.host in {'127.0.0.1', '::1', 'testclient'}
    if not key and not local:
        return JSONResponse({'error': 'remote_auth_required'}, status_code=403)
    if key and (len(key) < 32 or not secrets.compare_digest(request.headers.get('authorization', '').encode('utf-8'), ('Bearer ' + key).encode('utf-8'))):
        return JSONResponse({'error': 'unauthorized'}, status_code=401)
    try:
        if int(request.headers.get('content-length', '0')) > 65536:
            return JSONResponse({'error': 'request_too_large'}, status_code=413)
    except ValueError:
        return JSONResponse({'error': 'invalid_content_length'}, status_code=400)
    return await call_next(request)


@app.exception_handler(RequestValidationError)
async def invalid_request(request, error):
    # FastAPI's default validation detail can echo input secrets; never echo it.
    return JSONResponse({'error': 'invalid_manifest', 'fields': [list(e['loc']) for e in error.errors()]}, status_code=422)


@app.exception_handler(PublicationError)
async def publication_error(request, error):
    code = 404 if error.code == 'not_found' else 423 if error.code == 'live_disabled' else 409
    return JSONResponse({'error': error.code, 'message': str(error)}, status_code=code)


@app.post('/dry-runs')
def dry_run(submission: Submission):
    return PublicationService().dry_run(submission)


@app.get('/dry-runs/{job_id}')
def status(job_id: str):
    return PublicationService().status(job_id)


@app.post('/dry-runs/{job_id}/reconcile')
def reconcile(job_id: str):
    return PublicationService().reconcile(job_id)


@app.post('/publish')
def publish():
    PublicationService().live()

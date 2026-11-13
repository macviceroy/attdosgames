"""Allowlisted delivery bundle. No DBs, worker logs, input media or credentials."""
import tempfile
import zipfile
from pathlib import Path
from .media import digest

FILES=('video.mp4','cover.png','cover.jpg','captions.srt','script.txt','metadata.json','report.json','project.json')
def bundle(db,id):
    job=db.job(id)
    if job['kind']!='render' or job['state'] not in {'completed','qc_failed'}:
        raise ValueError('Exportação ainda não disponível')
    folder=db.root/'jobs'/id
    for name in FILES:
        path=folder/name
        if not path.is_file() or path.is_symlink():raise ValueError('Arquivo de exportação ausente')
        expected=job['result']['hashes'].get(name)
        if expected and digest(path)!=expected:raise ValueError('Integridade da exportação inválida')
    handle=tempfile.NamedTemporaryFile(prefix='delivery-',suffix='.zip',dir=db.root/'incoming',delete=False)
    path=Path(handle.name);handle.close()
    try:
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
            for name in FILES:archive.write(folder/name,name)
        return path
    except BaseException:path.unlink(missing_ok=True);raise

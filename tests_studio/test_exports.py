import io
import json
import time
import zipfile
from pathlib import Path
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient
from attstudio.api import create_app
from attstudio.models import Project
from attstudio.render import render
from attstudio.covers import generate
from attstudio.media import ff, input_args, digest

HEADERS={'X-ATT-Studio':'1'}

def frame(video,t,target):
    ff(['-ss',str(t),*input_args(video),'-frames:v','1',str(target)])
    with Image.open(target) as im:return np.array(im.convert('RGB').crop((70,700,990,1120))).astype(float)

def test_text_layers_cover_and_zip_real(tmp_path):
    source=tmp_path/'source.mp4'
    ff(['-f','lavfi','-i','testsrc2=s=320x240:r=30:d=2','-f','lavfi','-i','sine=frequency=440:duration=2','-c:v','libx264','-preset','ultrafast','-c:a','aac','-t','2',str(source)])
    with TestClient(create_app(tmp_path/'dados com espaços ç')) as client:
        r=client.post('/api/assets',params={'filename':'source.mp4','kind':'video','rights':'CC0 fixture original'},content=source.read_bytes(),headers=HEADERS)
        assert r.status_code==200,r.text
        asset=r.json();db=client.app.state.db
        plain=Project(name='Camadas',template='cinema',clips=[{'asset':asset['id'],'start':0,'end':2}],cover={'time':1,'title':'Capa independente'})
        project=plain.model_copy(deep=True)
        from attstudio.models import TextLayer
        project.text_layers=[TextLayer(text='Camada temporal de teste',start=.6,end=1.4,y=700,animation='none')]
        results={}
        for name,p in [('plain',plain),('layers',project)]:
            job,_=db.enqueue('render',{'project':p.model_dump()});folder=db.root/'jobs'/job['id'];folder.mkdir()
            result=render(db,{'project':p.model_dump()},folder,folder/'cancel');assert result['quality']['technical_pass'],result
            db.state(job['id'],'completed',result);results[name]=(job,folder,result)
        differences={}
        for t in [.2,1,1.8]:
            a=frame(results['plain'][1]/'video.mp4',t,tmp_path/f'a{t}.png')
            b=frame(results['layers'][1]/'video.mp4',t,tmp_path/f'b{t}.png')
            differences[t]=float(np.abs(a-b).mean())
        assert differences[1]>10,differences
        assert differences[.2]<2 and differences[1.8]<2,differences
        job,folder,result=results['layers']
        preview=tmp_path/'preview';preview.mkdir()
        generate(db,{'project':project.model_dump()},preview,preview/'cancel')
        assert digest(preview/'cover.png')==digest(folder/'cover.png')
        (folder/'worker.log').write_text('PRIVATE LOCAL DIAGNOSTIC')
        response=client.get('/api/jobs/'+job['id']+'/download')
        assert response.status_code==200,response.text
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            assert set(z.namelist())=={'video.mp4','cover.png','cover.jpg','captions.srt','script.txt','metadata.json','report.json','project.json'}
            assert z.read('video.mp4')==(folder/'video.mp4').read_bytes()
            assert json.loads(z.read('project.json'))['text_layers'][0]['text']=='Camada temporal de teste'
        assert not list((db.root/'incoming').glob('delivery-*.zip'))
        (folder/'video.mp4').write_bytes(b'tampered')
        assert client.get('/api/jobs/'+job['id']+'/download').status_code==409


def test_layer_bounds_and_unavailable_archive(tmp_path):
    from attstudio.models import TextLayer
    import pytest
    with pytest.raises(ValueError):TextLayer(text='x',start=1,end=.5)
    with pytest.raises(ValueError):Project(name='x',clips=[{'asset':'a'*32,'start':0,'end':1}],text_layers=[{'text':'x','end':2}])
    with TestClient(create_app(tmp_path/'dados com espaços ç')) as client:
        j,_=client.app.state.db.enqueue('render',{})
        assert client.get('/api/jobs/'+j['id']+'/download').status_code==409

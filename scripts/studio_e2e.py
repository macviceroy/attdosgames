"""Real MP4 end-to-end; no speech quality claim, no external media or publishing.
Run: uv run --extra studio python scripts/studio_e2e.py --output /absolute/test-dir
"""
import argparse
import json
import time
from pathlib import Path
from fastapi.testclient import TestClient
from attstudio.api import create_app
from attstudio.media import ff, digest
from attstudio.models import Project

H={'X-ATT-Studio':'1'}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    root=Path(args.output).resolve();root.mkdir(parents=True,exist_ok=True)
    source=root/'source.mp4';music=root/'music.wav';voice=root/'audio-track-test.wav'
    # Original procedural visuals and generated test signals: CC0. Not GTA gameplay or human narration.
    for i,color in enumerate(['purple','teal','orange']):
        ff(['-f','lavfi','-i',f'testsrc2=s=640x360:r=30:d=12','-f','lavfi','-i',f'sine=frequency={220+i*110}:duration=12','-vf',f'drawbox=x=0:y=0:w=200:h=360:color={color}:t=fill','-c:v','libx264','-preset','ultrafast','-c:a','aac','-t','12',str(root/f'input-{i}.mp4')])
    (root/'list.txt').write_text('\n'.join(f"file 'input-{i}.mp4'" for i in range(3)))
    ff(['-f','concat','-safe','1','-i','list.txt','-c','copy',str(source)],cwd=root)
    ff(['-f','lavfi','-i','sine=frequency=110:duration=8','-af','volume=0.3',str(music)])
    ff(['-f','lavfi','-i','sine=frequency=660:duration=4','-af',"volume='if(lt(mod(t,1),0.5),1,0)':eval=frame",str(voice)])
    evidence={'fixture_license':'CC0 original generated test patterns and tones','speech_tested':False,'exports':[]}
    with TestClient(create_app(root/'store')) as c:
        def post(url,data=None):
            r=c.post(url,json=data or {},headers=H);assert r.status_code==200,r.text;return r.json()
        def upload(path,kind):
            r=c.post('/api/assets',params={'filename':path.name,'kind':kind,'rights':'CC0 — original procedural test fixture'},content=path.read_bytes(),headers=H);assert r.status_code==200,r.text;return r.json()
        def wait(job):
            deadline=time.time()+600
            while time.time()<deadline:
                j=c.get('/api/jobs/'+job['id']).json()
                if j['state'] not in {'queued','running'}:
                    assert j['state']=='completed',json.dumps(j,ensure_ascii=False)
                    return j
                time.sleep(.3)
            raise TimeoutError(job['id'])
        a=upload(source,'video');m=upload(music,'audio');v=upload(voice,'audio')
        evidence['import']={'duration':a['duration'],'width':a['width'],'height':a['height'],'thumbnail_status':c.get('/api/assets/'+a['id']+'/thumbnail').status_code,'range_status':c.get('/api/assets/'+a['id']+'/file',headers={'Range':'bytes=0-99'}).status_code}
        for style in ['neon','arcade','cinema']:
            p=Project(name='Teste '+style,title='Seu vídeo. Sua identidade.',template=style,
                clips=[{'asset':a['id'],'start':1,'end':4,'zoom':True},{'asset':a['id'],'start':13,'end':16}],
                narration={'asset':v['id'],'volume':.8},music={'asset':m['id'],'volume':.2},original_volume=.4,
                captions={'style':'bounce' if style=='arcade' else 'minimal' if style=='cinema' else 'karaoke','cues':[{'start':0,'end':2,'text':'Teste visual ATT DOS GAMES'},{'start':2,'end':4,'text':'Sinais de áudio, sem voz humana'},{'start':4,'end':6,'text':'Exportação local em MP4'}]},
                script='Teste visual ATT DOS GAMES. Sinais de áudio, sem voz humana. Exportação local em MP4.',description='Demonstração técnica com mídia original; não é gameplay.',cover={'title':'Teste '+style.upper(),'color':{'neon':'#FF007A','arcade':'#FFC400','cinema':'#D6C5AB'}[style]})
            saved=post('/api/projects',p.model_dump());j=post('/api/projects/'+saved['id']+'/render');j=wait(j)
            duplicate=post('/api/projects/'+saved['id']+'/render');assert duplicate['id']==j['id']
            exports={}
            out=root/style;out.mkdir(exist_ok=True)
            for name in ['video.mp4','cover.png','cover.jpg','captions.srt','script.txt','metadata.json','report.json','project.json']:
                r=c.get(f"/api/jobs/{j['id']}/files/{name}");assert r.status_code==200,r.text;(out/name).write_bytes(r.content);exports[name]=digest(out/name)
                expected=j['result']['hashes'].get(name)
                if expected:assert exports[name]==expected
            evidence['exports'].append({'template':style,'job':j['id'],'qc':j['result']['quality'],'hashes':exports,'idempotency':True})
            print(style,'PASS',flush=True)
        analysis=wait(post('/api/analyze',{'asset':a['id'],'seconds':10}))
        candidates=analysis['result']['candidates'];assert len(candidates)>=3
        evidence['analysis']=analysis['result'];evidence['variations']=[]
        for i,part in enumerate(candidates[:3]):
            p=Project(name=f'Variação {i+1}',title=f'Momento {i+1}',clips=[{'asset':a['id'],'start':part['start'],'end':part['end']}])
            saved=post('/api/projects',p.model_dump());j=wait(post('/api/projects/'+saved['id']+'/render'))
            out=root/f'variation-{i+1}';out.mkdir(exist_ok=True)
            for name in ['video.mp4','cover.png','report.json']:
                r=c.get(f"/api/jobs/{j['id']}/files/{name}");assert r.status_code==200;(out/name).write_bytes(r.content)
            evidence['variations'].append({'start':part['start'],'end':part['end'],'job':j['id'],'quality':j['result']['quality']})
            print('variation',i+1,'PASS',flush=True)
        assert len({e['hashes']['video.mp4'] for e in evidence['exports']})==3
        assert c.post('/api/publish',headers=H).status_code==423
        evidence['publication_blocked']=True
    (root/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
    print('E2E PASS:',root/'evidence.json')
if __name__=='__main__':main()

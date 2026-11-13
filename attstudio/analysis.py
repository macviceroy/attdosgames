"""CPU heuristics: scene boundaries, sampled motion and audio energy, no LLM."""
import math
import wave
import numpy as np
import cv2
from scenedetect import open_video, SceneManager, ContentDetector
from .media import ff,input_args,Cancelled

def analyze(db,payload,folder,cancel):
    id=payload['asset'];asset=db.asset(id);path=db.path(id);length=payload['seconds']
    if asset['kind']!='video':raise ValueError('Selecione um vídeo')
    video=open_video(str(path));manager=SceneManager();manager.add_detector(ContentDetector(threshold=27,min_scene_len=15))
    manager.auto_downscale=False;manager.downscale=max(1,round(asset['width']/320))
    def callback(frame,number):
        if cancel.exists():raise Cancelled('Análise cancelada')
    # SceneManager callback fires on cuts; its stop flag is also watched by a monitor.
    import threading
    done=threading.Event()
    def monitor():
        while not done.wait(.2):
            if cancel.exists():manager.stop();return
    watch=threading.Thread(target=monitor,daemon=True);watch.start()
    try:manager.detect_scenes(video,callback=callback,show_progress=False)
    finally:done.set();watch.join()
    if cancel.exists():raise Cancelled('Análise cancelada')
    scenes=[{'start':a.get_seconds(),'end':b.get_seconds()} for a,b in manager.get_scene_list(start_in_scene=True)]
    if not scenes:scenes=[{'start':0,'end':asset['duration']}]
    # Sampling across the full source, rather than claiming semantic understanding.
    cap=cv2.VideoCapture(str(path));activity=[];previous=None
    try:
        for second in range(math.ceil(asset['duration'])):
            if cancel.exists():raise Cancelled('Análise cancelada')
            cap.set(cv2.CAP_PROP_POS_MSEC,second*1000);ok,frame=cap.read()
            if not ok:break
            gray=cv2.cvtColor(cv2.resize(frame,(160,90)),cv2.COLOR_BGR2GRAY)
            motion=float(np.abs(gray.astype(float)-previous).mean()/255) if previous is not None else 0
            activity.append(motion);previous=gray.astype(float)
    finally:cap.release()
    energy=np.zeros(math.ceil(asset['duration']))
    if asset['audio']:
        wav=folder/'energy.wav'
        try:
            ff([*input_args(path),'-vn','-ac','1','-ar','8000','-c:a','pcm_s16le',str(wav)],cancel=cancel)
            with wave.open(str(wav),'rb') as w:
                for i in range(len(energy)):
                    values=np.frombuffer(w.readframes(8000),dtype='<i2').astype(float)/32768
                    if len(values):energy[i]=np.sqrt(np.mean(values**2))
        finally:wav.unlink(missing_ok=True)
    starts=sorted({round(s['start'],3) for s in scenes}|{float(i) for i in np.arange(0,max(1,asset['duration']-length+.001),length)})
    candidates=[]
    for start in starts:
        end=min(start+length,asset['duration'])
        if end-start<min(length,asset['duration'])-.1:continue
        lo=int(start);hi=max(lo+1,math.ceil(end));motion=float(np.mean(activity[lo:hi])) if activity[lo:hi] else 0
        rms=float(np.mean(energy[lo:hi]));cuts=sum(start<s['start']<end for s in scenes)
        candidates.append({'start':start,'end':end,'duration':end-start,'motion':round(motion,4),'audio_rms':round(rms,4),'cuts':cuts,'score':round(motion*.6+min(rms*4,1)*.3+min(cuts/5,1)*.1,4)})
    selected=[]
    for c in sorted(candidates,key=lambda c:c['score'],reverse=True):
        if all(c['end']<=s['start'] or c['start']>=s['end'] for s in selected):selected.append(c)
        if len(selected)==6:break
    # Deterministic disjoint grid prevents a high-ranked offset from starving 3 clips.
    if len(selected)<min(3,int(asset['duration']//length)):
        selected=[c for c in candidates if abs(c['start']/length-round(c['start']/length))<.001][:6]
    for i,c in enumerate(selected):
        filename=f'moment-{i}.jpg'
        ff(['-ss',str(c['start']),*input_args(path),'-frames:v','1','-vf','scale=320:-2',str(folder/filename)],cancel=cancel)
        c['thumbnail']=filename
    return {'asset':id,'method':'PySceneDetect ContentDetector + sampled visual change + RMS','semantic_analysis':False,
            'warning':'Sugestões técnicas, sem previsão de viralização. Silêncio não é removido. Revise o contexto.',
            'scenes':scenes,'candidates':selected}

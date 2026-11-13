"""Small original procedural instrument loops; no downloaded/commercial recordings."""
import wave
import numpy as np
from .store import uid
from .media import digest

STYLES={'synthwave':100,'eletronica':128,'lofi':76}
def generate(db,style):
    if style not in STYLES:raise ValueError('Estilo inválido')
    rate=24000;bpm=STYLES[style];beat=60/bpm;duration=beat*16
    count=round(duration*rate);sound=np.zeros(count);rng=np.random.default_rng(2026)
    # Original deterministic four-bar motif, not a transcription of a song.
    notes=[45,48,52,55,43,47,50,55,41,45,48,52,43,47,50,54]
    for i,note in enumerate(notes):
        pos=round(i*beat*rate);n=min(round(beat*rate),count-pos);t=np.arange(n)/rate
        hz=440*2**((note-69)/12);env=(1-np.exp(-t*60))*np.exp(-t*(4 if style=='lofi' else 2.5))
        harmonics=np.sin(2*np.pi*hz*t)
        if style!='lofi':harmonics+=.25*np.sin(2*np.pi*hz*2*t)+.1*np.sin(2*np.pi*hz*3*t)
        sound[pos:pos+n]+=.18*harmonics*env
        kick=np.sin(2*np.pi*(48*t+4*(1-np.exp(-t*24))))*np.exp(-t*18)
        sound[pos:pos+n]+=.25*kick
        if i%2:
            sound[pos:pos+n]+=.035*rng.uniform(-1,1,n)*np.exp(-t*35)
    sound*=.7/max(.7,float(np.max(np.abs(sound))))
    id=uid();folder=db.root/'assets'/id;folder.mkdir();path=folder/'source.wav'
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes((sound*32767).astype('<i2').tobytes())
    a={'id':id,'name':f'ATT original — {style}.wav','extension':'.wav','kind':'audio','bytes':path.stat().st_size,'rights':'CC0-1.0 — composição procedural original ATT Studio; sem gravações comerciais',
       'sha256':digest(path),'duration':count/rate,'width':0,'height':0,'audio':True,'bpm':bpm,'beats':[round(i*beat,4) for i in range(16)]}
    db.add_asset(a);return a

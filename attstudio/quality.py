import re
from .media import probe, run, input_args
from .runtime import executable
from .captions import srt

def inspect(folder,p,cancel=None):
    path=folder/'video.mp4';m=probe(path)
    v=next(s for s in m['streams'] if s['codec_type']=='video');a=next(s for s in m['streams'] if s['codec_type']=='audio')
    run([executable('ffmpeg'),'-v','error','-xerror',*input_args(path),'-f','null','-'],cancel=cancel)
    # Audio/black diagnostics use captured stderr via a local file, no shell.
    import subprocess
    result=subprocess.run([executable('ffmpeg'),'-hide_banner',*input_args(path),'-af','volumedetect','-vf','blackdetect=d=0.5:pix_th=0.08','-f','null','-'],capture_output=True,text=True,timeout=300)
    log=result.stderr
    peak=re.search(r'max_volume: ([-\w.]+) dB',log)
    peak_db=float(peak[1]) if peak else float('-inf')
    black=[{'start':float(x),'end':float(y),'duration':float(z)} for x,y,z in re.findall(r'black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)',log)]
    checks={'decode':result.returncode==0,'resolution':(v['width'],v['height'])==(1080,1920),
            'codecs':v['codec_name']=='h264' and a['codec_name']=='aac',
            'duration':abs(float(m['format']['duration'])-p.duration)<.2,
            'audio_timeline':abs(float(a.get('duration',0))-p.duration)<.2,
            'srt_matches_project':(folder/'captions.srt').read_text(encoding='utf-8')==srt(p.captions.cues),
            'no_unexpected_black':not black,'audible_audio':peak_db>-55,
            'no_peak_clipping':peak_db<0}
    return {'technical_pass':all(checks.values()),'checks':checks,'peak_db':peak_db if peak else None,'black_intervals':black,
            'human_review':['Sotaque pt-BR e pronúncia','Correspondência de cada palavra ao áudio','Legibilidade no telefone','Conteúdo e direitos'],
            'publication_allowed':False}

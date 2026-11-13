import json
import shutil
import textwrap
from PIL import Image, ImageDraw, ImageOps
from attgames.editor import font
from . import captions
from .media import ff, input_args, probe, digest, validate_project, amf_available
from .models import Project

PALETTE={'neon':'#FF007A','arcade':'#FFC400','cinema':'#D6C5AB'}

def text_card(title,style,size=56,color=None,width=920,font_name="DejaVu Sans"):
    from .fonts import load
    def chosen(size):return load(font_name,size)
    color=color or PALETTE[style]
    im=Image.new('RGBA',(width,420),(0,0,0,0));d=ImageDraw.Draw(im)
    if style=='neon':
        for inset,alpha in [(0,30),(6,60),(12,120)]:
            d.rounded_rectangle((inset,inset,width-inset-1,395-inset),radius=28,outline=color+'%02x'%alpha,width=5)
        d.rounded_rectangle((18,18,width-19,380),radius=22,fill='#140B27DE',outline=color,width=3)
    elif style=='arcade':
        d.rectangle((0,0,width-1,390),fill='#0B0B14E0',outline=color,width=12)
        for x in range(20,width-20,40):d.rectangle((x,20,x+16,32),fill=color)
    else:
        d.rectangle((0,10,width,390),fill='#08080CC0');d.line((36,350,width-36,350),fill=color,width=2)
    lines=[];line=''
    # Pixel width measurement, not character-count clipping.
    for word in title.split():
        trial=(line+' '+word).strip()
        if d.textlength(trial,font=chosen(size))>width-85 and line:
            lines.append(line);line=word
        else:line=trial
    if line:lines.append(line)
    if len(lines)>4 or any(d.textlength(x,font=chosen(size))>width-85 for x in lines):
        if size>28:return text_card(title,style,size-4,color,width,font_name)
        raise ValueError('Título longo demais para a área segura')
    y=80
    for line in lines:
        d.text((40,y),line,font=chosen(size),fill='white',stroke_width=1);y+=size+12
    d.text((40,315),'ATT DOS GAMES  /  @attdosgames',font=font(25),fill=color)
    return im

def make_cover(db,p,video,folder,cancel):
    if p.cover.image:
        with Image.open(db.path(p.cover.image)) as original:im=ImageOps.fit(original.convert('RGB'),(1080,1920))
    else:
        ff(['-ss',str(p.cover.time),*input_args(video),'-frames:v','1',str(folder/'frame.png')],cancel=cancel)
        with Image.open(folder/'frame.png') as original:im=original.convert('RGB')
    im=ImageOps.fit(im,(1080,1920)).convert('RGBA')
    overlay=text_card(p.cover.title or p.title,p.template,p.cover.size,p.cover.color,font_name=p.cover.font)
    im.alpha_composite(overlay,(70,p.cover.y));im.convert('RGB').save(folder/'cover.png')
    im.convert('RGB').save(folder/'cover.jpg',quality=94)

def render(db,payload,folder,cancel):
    p=Project.model_validate(payload['project']);assets=validate_project(db,p)
    encoder='libx264'
    if p.encoder=='amd':
        if not amf_available():raise ValueError('AMD AMF não passou no teste real. Selecione CPU.')
        encoder='h264_amf'
    codec=['-c:v',encoder]+(['-preset','veryfast','-crf','23'] if encoder=='libx264' else ['-quality','balanced','-b:v','8M'])
    work=folder/'temp';work.mkdir(exist_ok=True)
    (work/'fonts').mkdir(exist_ok=True)
    from attgames.editor import PROJECT
    from .fonts import path as font_path
    for name in {p.captions.font,p.cover.font,'DejaVu Sans'}:
        f=font_path(name);shutil.copy2(f,work/'fonts'/f.name)
    try:
        for i,c in enumerate(p.clips):
            seconds=round((c.end-c.start)*30)/30
            # Crop the chosen horizontal subject position; zoom keeps a stable center.
            vf=f'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(iw-1080)*{c.focus_x}:(ih-1920)/2,setsar=1,fps=30'
            if c.zoom:
                vf+=",zoompan=z='1+0.00015*on':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30"
            if p.template=='neon':vf+=',eq=saturation=1.18:contrast=1.04,drawbox=x=35:y=240:w=6:h=1280:color=0xFF007A:t=fill'
            if p.template=='arcade':vf+=',scale=270:480:flags=neighbor,scale=1080:1920:flags=neighbor,drawgrid=w=1080:h=8:t=1:c=black@0.16'
            if p.template=='cinema':vf+=',eq=saturation=0.82:contrast=1.08,vignette=PI/5'
            if p.transition=='fade':
                length=.18 if p.template!='arcade' else .07
                vf+=f',fade=t=in:st=0:d={length},fade=t=out:st={seconds-length}:d={length}'
            args=['-ss',str(c.start),*input_args(db.path(c.asset))]
            if not db.asset(c.asset)['audio']:args+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
            args+=['-map','0:v:0','-map','0:a:0' if db.asset(c.asset)['audio'] else '1:a:0','-t',str(seconds),'-vf',vf,'-af',f'aresample=48000,aformat=channel_layouts=stereo,volume={p.original_volume},apad',*codec,'-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-ac','2','-threads','2',f'part-{i}.mp4']
            ff(args,cwd=work,cancel=cancel)
        (work/'concat.txt').write_text('\n'.join(f"file 'part-{i}.mp4'" for i in range(len(p.clips))),encoding='utf-8')
        ff(['-f','concat','-safe','1','-i','concat.txt','-c','copy','base.mp4'],cwd=work,cancel=cancel)
        (work/'captions.ass').write_text(captions.ass(p),encoding='utf-8')
        text_card(p.title,p.template).save(work/'title.png')
        args=[*input_args('base.mp4'),'-loop','1',*input_args('title.png')]
        graph=["[0:v][1:v]overlay=x=70:y='180+30*exp(-6*t)':enable='lt(t,3)'[title]",'[title]ass=filename=captions.ass:fontsdir=fonts[v]']
        audio=['[0:a]'];next_index=2
        narration=None;music=None
        for name,track in [('narr',p.narration),('music',p.music)]:
            if track:
                if name=='music':args+=['-stream_loop','-1']
                args+=input_args(db.path(track.asset));delay=round(track.offset*1000)
                graph.append(f'[{next_index}:a]aresample=48000,aformat=channel_layouts=stereo,volume={track.volume},adelay={delay}|{delay},apad,atrim=duration={p.duration}[{name}]')
                if name=='narr':narration='[narr]'
                else:music='[music]'
                next_index+=1
        if narration and music and p.ducking:
            graph+=['[narr]asplit=2[voice][side]','[music][side]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[duck]']
            narration='[voice]';music='[duck]'
        audio += [x for x in [narration,music] if x]
        graph.append(''.join(audio)+f'amix=inputs={len(audio)}:duration=longest:normalize=0,alimiter=limit=0.95:level=false:latency=true,atrim=duration={p.duration}[a]')
        ff([*args,'-filter_complex',';'.join(graph),'-map','[v]','-map','[a]','-t',str(p.duration),*codec,'-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-ar','48000','-threads','2','-movflags','+faststart',str(folder/'video.mp4')],cwd=work,cancel=cancel)
        make_cover(db,p,folder/'video.mp4',folder,cancel)
        (folder/'captions.srt').write_text(captions.srt(p.captions.cues),encoding='utf-8')
        (folder/'script.txt').write_text(p.script,encoding='utf-8')
        (folder/'project.json').write_text(p.model_dump_json(indent=2),encoding='utf-8')
        metadata={'title':p.title,'description':p.description,'hashtags':p.hashtags,'duration':p.duration,'language':'pt-BR'}
        (folder/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
        from .quality import inspect
        qc=inspect(folder,p,cancel)
        report={'version':1,'quality':qc,'assets':assets,'template':p.template,'encoder':encoder,
                'voice':{'provider':'imported' if p.narration else None,'preferred':'ATT DOS GAMES - Brasileiro Alex','pt_BR_accent':'human_review_required'},
                'rights':'User declarations, not independently verified licenses','publication_allowed':False,
                'hashes':{x.name:digest(x) for x in folder.iterdir() if x.is_file() and x.name not in {'cancel','frame.png','worker.log'}}}
        (folder/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        return report
    finally:
        shutil.rmtree(work,ignore_errors=True)
        (folder/'frame.png').unlink(missing_ok=True)

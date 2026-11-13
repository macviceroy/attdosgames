import re
import textwrap
from .models import Cue
from attgames.editor import timestamp

def srt(cues):
    return '\n'.join(f'{i+1}\n{timestamp(c.start)} --> {timestamp(c.end)}\n{c.text}\n' for i,c in enumerate(cues))

def parse_srt(text):
    def seconds(s):
        h,m,rest=s.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(rest)
    cues=[]
    for block in re.split(r'\n\s*\n',text.replace('\r','').strip()):
        lines=block.splitlines()
        if len(lines)<3 or ' --> ' not in lines[1]:raise ValueError('SRT inválido')
        a,b=lines[1].split(' --> ')
        cues.append(Cue(start=seconds(a),end=seconds(b),text=' '.join(lines[2:])))
    return cues

def ass_time(t):
    cs=round(t*100);return f'{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}'

def ass(p):
    c=p.captions; rgb=c.color[1:];color='&H00'+rgb[4:6]+rgb[2:4]+rgb[:2]
    header=f'''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{c.font},{c.size},{color},&H007A00FF,&H00140B0B,&H90000000,-1,0,0,0,100,100,0,0,1,3,1,2,110,160,350,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    for cue in c.cues:
        text='\\N'.join(textwrap.wrap(cue.text, max(12,int(1050/c.size*1.25))))
        tag=f'\\an2\\pos(515,{c.y})'
        if c.style=='neon':tag+='\\bord5\\blur1\\3c&H007A00FF&\\fad(60,60)'
        if c.style=='bounce':tag+='\\fscx85\\fscy85\\t(0,120,\\fscx105\\fscy105)\\t(120,230,\\fscx100\\fscy100)'
        # Each cue is a measured word/phrase: never manufacture word timestamps.
        if c.style=='karaoke':tag+=f'\\kf{round((cue.end-cue.start)*100)}'
        if c.style=='word':tag+='\\bord6\\3c&H00FF00A1&\\1c&H0000C4FF&'
        header+=f'Dialogue: 0,{ass_time(cue.start)},{ass_time(cue.end)},Default,,0,0,0,,{{{tag}}}{text}\n'
    return header

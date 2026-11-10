import hashlib
import json
import math
import subprocess
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .tts import synthesize

COLORS = ['#FF007A', '#A100FF', '#00E5FF', '#FFC400']
PROJECT = Path(__file__).resolve().parents[1]


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=300)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    return result.stdout


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size, title=False):
    name = 'BebasNeue-Regular.ttf' if title else 'Montserrat-Regular.ttf'
    candidate = PROJECT / 'brand' / name
    # Custom fonts require a sidecar license; otherwise use bundled DejaVu.
    if candidate.exists():
        if not candidate.with_suffix('.LICENSE.txt').is_file():
            raise ValueError(f'Licença da fonte ausente: {candidate.name}')
        return ImageFont.truetype(str(candidate), size)
    return ImageFont.truetype(str(PROJECT / 'brand' / 'DejaVuSans-Bold.ttf'), size)


def card(path, theme, caption, index, total, cover=False):
    im = Image.new('RGB', (1080, 1920), '#0B0B14')
    d = ImageDraw.Draw(im)
    accent = COLORS[index % len(COLORS)]
    for offset in range(0, 500, 35):
        d.line((0, 360 + offset, 1080, 80 + offset), fill='#271338', width=3)
    d.rounded_rectangle((55, 70, 1025, 165), radius=18, outline=accent, width=4)
    d.text((90, 91), 'ATT DOS GAMES', font=font(46, True), fill='white')
    d.text((80, 225), 'GTA VI', font=font(150, True), fill=accent, stroke_width=2)
    d.text((85, 420), 'RADAR • EDIÇÃO DE TESTE', font=font(34), fill='#00E5FF')
    # Original abstract skyline: no Rockstar or third-party imagery.
    for n in range(12):
        x = n * 100 - 30
        top = 850 - ((n * 73 + index * 37) % 300)
        d.rectangle((x, top, x + 74, 1100), fill='#18102D', outline=accent, width=3)
        for y in range(top + 22, 1060, 45):
            d.rectangle((x + 18, y, x + 30, y + 12), fill='#FFC400')
    label = theme if cover else caption
    lines = textwrap.wrap(label.upper(), width=22, break_long_words=True)
    y = 1150
    for line in lines[:5]:
        d.text((85, y), line, font=font(54, True), fill='white', stroke_width=1)
        y += 76
    d.rectangle((85, 1600, 995, 1610), fill='#29203C')
    d.rectangle((85, 1600, 85 + int(910 * (index + 1) / total), 1610), fill=accent)
    d.text((85, 1660), '@attdosgames', font=font(42), fill='#00E5FF')
    d.text((85, 1730), 'DEMO • NÃO É NOTÍCIA VERIFICADA', font=font(30), fill='#FFC400')
    im.save(path)


def timestamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def script(theme, duration):
    phrases = ['GTA seis: cuidado com rumores!', 'Este é um vídeo demonstrativo.',
               'O tema de hoje é:', theme + '.',
               'Vamos separar expectativa de informação.', 'Procure sempre a fonte original.',
               'Confira a data da publicação.', 'Trailer público não significa licença.',
               'Este cenário é arte original.', 'Nenhuma cena do jogo foi usada.',
               'Notícias precisam de confirmação oficial.', 'Rumor não é anúncio da Rockstar.',
               'Acompanhe o arroba ATT dos Games.', 'Salve para conferir as fontes.']
    count = math.ceil(duration / 2.5)
    phrases = (phrases * math.ceil(count / len(phrases)))[:count]
    # Exact frame-aligned timeline at 30 fps.
    frames = round(duration * 30)
    return [dict(text=p, start=round(i * frames / count) / 30,
                 end=round((i + 1) * frames / count) / 30) for i, p in enumerate(phrases)]


def render(folder, theme, duration):
    scenes = script(theme, duration)
    (folder / 'script.json').write_text(json.dumps(scenes, ensure_ascii=False, indent=2))
    subtitles = []
    assets = []
    for i, scene in enumerate(scenes):
        image = folder / f'scene-{i:02}.png'
        raw = folder / f'voice-{i:02}.wav'
        clip = folder / f'clip-{i:02}.mp4'
        card(image, theme, scene['text'], i, len(scenes))
        voice = synthesize(scene['text'], raw)
        audio_duration = float(probe(raw)['format']['duration'])
        seconds = scene['end'] - scene['start']
        tempo = max(0.5, audio_duration / (seconds - 0.12))
        filters = []
        while tempo > 2:
            filters.append('atempo=2')
            tempo /= 2
        filters.append(f'atempo={tempo:.8f}')
        filters.extend(['apad', f'atrim=duration={seconds}', 'aresample=48000'])
        frames = round(seconds * 30)
        run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-loop', '1', '-i', str(image),
             '-i', str(raw), '-vf',
             f"zoompan=z='1+0.00025*on':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30,fade=t=in:st=0:d=0.10,fade=t=out:st={seconds-.10}:d=0.10",
             '-af', ','.join(filters), '-frames:v', str(frames), '-t', str(seconds),
             '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-pix_fmt', 'yuv420p',
             '-c:a', 'aac', '-b:a', '128k', '-threads', '2', str(clip)])
        subtitles.append(f"{i+1}\n{timestamp(scene['start'])} --> {timestamp(scene['end'])}\n{scene['text']}\n")
        assets.append({'file': image.name, 'sha256': digest(image), 'license': 'CC0-1.0',
                       'creator': 'ATT DOS GAMES pipeline', 'origin': 'procedural original artwork',
                       'commercial_use': True})
    (folder / 'legendas.srt').write_text('\n'.join(subtitles), encoding='utf-8')
    (folder / 'concat.txt').write_text('\n'.join(f"file 'clip-{i:02}.mp4'" for i in range(len(scenes))))
    run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'concat', '-safe', '1', '-i',
         str(folder / 'concat.txt'), '-c', 'copy', '-movflags', '+faststart', str(folder / 'final.mp4')])
    card(folder / 'capa.png', theme, theme, 0, 1, True)
    return scenes, assets, voice

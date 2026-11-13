"""Optional trusted HyperFrames template -> MP4 asset for the existing FFmpeg timeline.
No user-supplied HTML/JavaScript is accepted. This CLI never publishes.
"""
import argparse
import html
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from .media import probe

def create(title, output, cli=None):
    if not 1<=len(title)<=70:raise ValueError('Título: 1 a 70 caracteres')
    root=Path(__file__).resolve().parents[1]
    cli=Path(cli or root/'integrations/hyperframes/node_modules/hyperframes/dist/cli.js').resolve()
    if not cli.is_file():raise ValueError('Instale a integração opcional com npm ci --ignore-scripts em integrations/hyperframes')
    output=Path(output).resolve();output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists():raise ValueError('Saída já existe: escolha outro nome')
    env={**os.environ,'HYPERFRAMES_NO_TELEMETRY':'1','HYPERFRAMES_NO_UPDATE_CHECK':'1','DO_NOT_TRACK':'1'}
    with tempfile.TemporaryDirectory(prefix='att-motion-') as tmp:
        folder=Path(tmp)
        env['HYPERFRAMES_CACHE_DIR']=str(folder/'cache')
        template=(Path(__file__).parent/'static/motion-template.html').read_text(encoding='utf-8')
        (folder/'index.html').write_text(template.replace('SEU PRÓXIMO<br>SHORT.',html.escape(title)),encoding='utf-8')
        shutil.copy2(root/'brand/DejaVuSans-Bold.ttf',folder/'font.ttf')
        subprocess.run(['node',str(cli),'render',str(folder),'--output',str(output),'--fps','30','--workers','1','--quality','draft','--no-page-side-compositing'],env=env,check=True,timeout=300)
    media=probe(output);v=next(s for s in media['streams'] if s['codec_type']=='video')
    if (v['width'],v['height'])!=(1080,1920) or abs(float(media['format']['duration'])-3)>.1:
        raise ValueError('HyperFrames produziu formato inesperado')
    return output

def main():
    p=argparse.ArgumentParser(description='Título neon HTML/CSS de 3 s para importar no Studio')
    p.add_argument('--title',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--cli',type=Path)
    args=p.parse_args();print(create(args.title,args.output,args.cli))
if __name__=='__main__':main()

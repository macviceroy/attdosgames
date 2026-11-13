"""Authorized URL ingestion through yt-dlp. No cookies, playlists or DRM bypass."""
import shutil
from pathlib import Path
from urllib.parse import urlsplit

from .media import digest, ff, input_args, inspect_upload
from .store import uid

ALLOWED={'youtube.com','www.youtube.com','m.youtube.com','youtu.be','instagram.com','www.instagram.com',
         'tiktok.com','www.tiktok.com','vm.tiktok.com'}


def validate_url(url: str) -> str:
    parsed=urlsplit(url.strip())
    host=(parsed.hostname or '').lower()
    if parsed.scheme!='https' or host not in ALLOWED or parsed.username or parsed.password:
        raise ValueError('Use uma URL HTTPS do YouTube, Instagram ou TikTok')
    return url.strip()


def download(db,payload,folder,cancel):
    if cancel.exists():raise RuntimeError('Importação cancelada')
    url=validate_url(payload['url']);rights=payload['rights'].strip()
    target=folder/'download.%(ext)s'
    from yt_dlp import YoutubeDL
    options={'outtmpl':str(target),'noplaylist':True,'playlist_items':'1','max_filesize':512*1024*1024,
             'format':'bv*[height<=1080]+ba/b[height<=1080]','merge_output_format':'mp4',
             'quiet':True,'no_warnings':True,'socket_timeout':25,'retries':2,
             'writesubtitles':False,'writeautomaticsub':False,'writethumbnail':False,
             'overwrites':False,'restrictfilenames':True}
    try:
        with YoutubeDL(options) as client:metadata=client.extract_info(url,download=True)
    except Exception as exc:
        raise ValueError('A plataforma recusou a importação ou o link não é acessível. Não usamos cookies nem burlamos restrições.') from exc
    candidates=[p for p in folder.glob('download.*') if p.suffix.lower() in {'.mp4','.webm','.mkv','.mov'}]
    if len(candidates)!=1:raise RuntimeError('A importação não produziu um único vídeo válido')
    source=candidates[0];info=inspect_upload(source,'video')
    asset_id=uid();asset_folder=db.root/'assets'/asset_id;asset_folder.mkdir()
    destination=asset_folder/('source'+source.suffix.lower())
    try:
        shutil.move(str(source),destination)
        ff([*input_args(destination),'-frames:v','1','-vf','scale=320:-2',str(asset_folder/'thumbnail.jpg')],timeout=60)
        name=(metadata.get('title') or 'Vídeo importado')[:140]+source.suffix.lower()
        asset={'id':asset_id,'name':name,'extension':source.suffix.lower(),'kind':'video',
               'bytes':destination.stat().st_size,'rights':rights,'source_url':url,
               'source_provider':metadata.get('extractor_key'),'sha256':digest(destination),**info}
        db.add_asset(asset)
        return {'asset':asset,'notice':'Importado mediante declaração de autorização; confirme também os termos da plataforma.'}
    except BaseException:
        shutil.rmtree(asset_folder,ignore_errors=True);raise

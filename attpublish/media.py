"""Validate real inputs and create local upload candidates. No HTTP clients."""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from fractions import Fraction
from pathlib import Path
from PIL import Image, ImageCms
from .models import PublicationError


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def execute(args, timeout=180):
    try:
        result = subprocess.run(args, capture_output=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as error:
        raise PublicationError('media_tool_failed', type(error).__name__) from error
    if result.returncode:
        # Provider credentials are never arguments to media tools.
        raise PublicationError('invalid_media', 'FFmpeg/ffprobe rejeitou a mídia: ' + result.stderr.decode(errors='replace')[-800:])
    return result.stdout


def probe(path):
    return json.loads(execute(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))


def validate(video, cover):
    for path, suffix in [(video, '.mp4'), (cover, '.png')]:
        if not path.is_file() or path.suffix.lower() != suffix or path.stat().st_size == 0:
            raise PublicationError('missing_or_invalid_file', f'Arquivo local {suffix} ausente, vazio ou inválido')
    if video.stat().st_size > 300_000_000 or cover.stat().st_size > 20_000_000:
        raise PublicationError('file_too_large', 'Limite: vídeo 300 MB; PNG de entrada 20 MB (política local)')
    try:
        with Image.open(cover) as image:
            if image.format != 'PNG' or image.size != (1080, 1920):
                raise PublicationError('invalid_cover', 'Capa deve ser PNG 1080x1920')
            image.verify()
    except (OSError, ValueError, Image.DecompressionBombError) as error:
        if isinstance(error, PublicationError):
            raise
        raise PublicationError('invalid_cover', 'PNG corrompido ou não suportado') from error
    media = probe(video)
    videos = [s for s in media['streams'] if s['codec_type'] == 'video']
    audios = [s for s in media['streams'] if s['codec_type'] == 'audio']
    if len(videos) != 1 or len(audios) != 1:
        raise PublicationError('invalid_streams', 'Exigido um stream de vídeo e um de áudio')
    v, a = videos[0], audios[0]
    duration = float(media['format']['duration'])
    fps = float(Fraction(v['avg_frame_rate']))
    checks = {'mp4': 'mp4' in media['format']['format_name'].split(','),
              'duration_3_to_180': 3 <= duration <= 180.2,
              'vertical_1080x1920': (v['width'], v['height']) == (1080, 1920),
              'video_h264_yuv420p': v['codec_name'] == 'h264' and v.get('pix_fmt') == 'yuv420p',
              'frame_rate_23_to_60': 23 <= fps <= 60,
              'audio_aac': a['codec_name'] == 'aac',
              'audio_sample_rate_channels': int(a['sample_rate']) <= 48000 and a['channels'] in (1, 2),
              'bitrate_under_25mbps': int(v.get('bit_rate', 0)) <= 25_000_000,
              'progressive': v.get('field_order', 'unknown') in ('progressive', 'unknown')}
    if not all(checks.values()):
        raise PublicationError('unsupported_media_profile', 'Perfil não suportado: ' + ', '.join(k for k, ok in checks.items() if not ok))
    execute(['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-f', 'null', '-'])
    return {'checks': checks, 'duration': duration, 'fps': fps,
            'platform_acceptance_verified': False,
            'source_video_sha256': sha256(video), 'source_cover_sha256': sha256(cover)}


def prepare(video, cover, root):
    video, cover = video.resolve(), cover.resolve()
    validation = validate(video, cover)
    key = hashlib.sha256((validation['source_video_sha256'] + validation['source_cover_sha256']).encode()).hexdigest()
    assets = Path(root) / 'assets'
    assets.mkdir(parents=True, exist_ok=True)
    destination = assets / key
    if not destination.exists():
        scratch = Path(tempfile.mkdtemp(prefix='prepare-', dir=assets))
        try:
            # Normalize container flags only; video/audio are not re-encoded.
            execute(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-map', '0:v:0', '-map', '0:a:0',
                     '-c', 'copy', '-movflags', '+faststart', '-use_editlist', '0', str(scratch / 'video.mp4')])
            shutil.copyfile(cover, scratch / 'cover.png')
            with Image.open(cover) as image:
                rgba = image.convert('RGBA')
                rgb = image.convert('RGB')
                target_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
                if image.info.get('icc_profile'):
                    import io
                    rgb = ImageCms.profileToProfile(rgb, ImageCms.ImageCmsProfile(io.BytesIO(image.info['icc_profile'])), target_profile, outputMode='RGB')
                background = Image.new('RGB', image.size, '#0B0B14')
                background.paste(rgb, mask=rgba.getchannel('A'))
                background.save(scratch / 'cover-instagram.jpg', quality=92, icc_profile=target_profile.tobytes())
            if (scratch / 'cover-instagram.jpg').stat().st_size > 8_000_000:
                raise PublicationError('instagram_cover_too_large', 'JPEG excede 8 MB')
            if sha256(video) != validation['source_video_sha256'] or sha256(cover) != validation['source_cover_sha256']:
                raise PublicationError('input_changed', 'Entradas alteradas durante preparação')
            execute(['ffmpeg', '-v', 'error', '-xerror', '-i', str(scratch / 'video.mp4'), '-f', 'null', '-'])
            manifest = {'validation': validation, 'hashes': {p.name: sha256(p) for p in scratch.iterdir()}}
            (scratch / 'manifest.json').write_text(json.dumps(manifest, indent=2))
            try:
                os.rename(scratch, destination)
            except OSError:
                if not destination.is_dir():
                    raise
        except (OSError, ValueError, ImageCms.PyCMSError) as error:
            if isinstance(error, PublicationError):
                raise
            raise PublicationError('asset_preparation_failed', type(error).__name__) from error
        finally:
            if scratch.exists():
                shutil.rmtree(scratch)
    manifest = json.loads((destination / 'manifest.json').read_text())
    if manifest['validation']['source_video_sha256'] != validation['source_video_sha256'] or manifest['validation']['source_cover_sha256'] != validation['source_cover_sha256']:
        raise PublicationError('asset_integrity', 'Manifesto não corresponde às entradas')
    if set(manifest['hashes']) != {'video.mp4', 'cover.png', 'cover-instagram.jpg'}:
        raise PublicationError('asset_integrity', 'Manifesto de artefatos incompleto')
    if not all((destination / name).is_file() and sha256(destination / name) == value for name, value in manifest['hashes'].items()):
        raise PublicationError('asset_integrity', 'Artefatos preparados foram alterados')
    return {'directory': str(destination), 'validation': validation, 'hashes': manifest['hashes']}

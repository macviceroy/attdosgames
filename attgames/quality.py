import json
import re
import struct
import subprocess
from pathlib import Path
from .editor import probe, digest, timestamp


def inspect(folder: Path, expected: float):
    checks = {}
    try:
        report = json.loads((folder / 'relatorio.json').read_text())
        media = probe(folder / 'final.mp4')
        video = next(s for s in media['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in media['streams'] if s['codec_type'] == 'audio')
        actual = float(media['format']['duration'])
        checks['duration'] = abs(actual - expected) <= 0.20
        checks['resolution'] = (video['width'], video['height']) == (1080, 1920)
        checks['codecs'] = video['codec_name'] == 'h264' and audio['codec_name'] == 'aac'
        checks['audio_timeline'] = abs(float(audio['duration']) - expected) <= .20
        # Decode all video/audio: ffprobe alone does not detect damaged payloads.
        decoded = subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(folder / 'final.mp4'),
                                  '-f', 'null', '-'], capture_output=True, timeout=180)
        checks['decode'] = decoded.returncode == 0
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(folder / 'final.mp4'), '-vn',
                              '-ac', '1', '-ar', '8000', '-f', 's16le', '-'],
                             capture_output=True, check=True, timeout=180).stdout
        samples = struct.unpack('<' + 'h' * (len(raw) // 2), raw)
        checks['audible_audio'] = bool(samples) and max(abs(s) for s in samples) > 200
        scenes = json.loads((folder / 'script.json').read_text())
        checks['cuts_1_to_3_seconds'] = all(1 <= s['end'] - s['start'] <= 3 for s in scenes)
        checks['speech_speed'] = all(float(probe(folder / f'voice-{i:02}.wav')['format']['duration']) / (s['end']-s['start']-.12) <= 2.0 for i,s in enumerate(scenes))
        checks['timeline'] = (scenes[0]['start'] == 0 and abs(scenes[-1]['end'] - expected) < .04
                              and all(abs(a['end']-b['start']) < .001 for a,b in zip(scenes, scenes[1:])))
        expected_srt = '\n'.join(f"{i+1}\n{timestamp(s['start'])} --> {timestamp(s['end'])}\n{s['text']}\n"
                                 for i,s in enumerate(scenes))
        checks['subtitle_phrase_sync'] = (folder / 'legendas.srt').read_text() == expected_srt
        checks['inputs_and_outputs_integrity'] = all((folder / name).is_file() and digest(folder / name) == sha
                                                      for name, sha in report['hashes'].items())
        checks['rights'] = bool(report['assets']) and all(a['commercial_use'] and a['license'] == 'CC0-1.0'
                                                                         for a in report['assets'])
        checks['pt_BR_voice_selection'] = report['voice']['voice'] == 'pt-br' and report['voice']['language'] == 'pt-BR'
    except (OSError, ValueError, KeyError, StopIteration, subprocess.SubprocessError) as exc:
        checks['inspection_error'] = str(exc)
    passed = bool(checks) and all(v is True for v in checks.values())
    return {'technical_pass': passed, 'checks': checks,
            'publication_allowed': False,
            'blocking_reasons': ['Fase 1: publicação desativada', 'Revisão humana de sotaque, conteúdo e direitos pendente',
                                 'Demo sem pesquisa factual: não publicar como notícia']}

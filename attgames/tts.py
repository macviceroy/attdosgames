"""eSpeak NG: seleção explícita brasileira; síntese serial em processo isolado."""
import ctypes as C
import wave
from pathlib import Path
import espeakng_loader


def synthesize(text: str, output: Path) -> dict:
    lib = espeakng_loader.load_library()
    if lib is None:
        raise RuntimeError('Biblioteca eSpeak NG indisponível')
    lib.espeak_Initialize.argtypes = [C.c_int, C.c_int, C.c_char_p, C.c_int]
    rate = lib.espeak_Initialize(2, 0, espeakng_loader.get_data_path().encode(), 0)
    if rate <= 0:
        raise RuntimeError('Falha ao inicializar TTS')
    lib.espeak_SetVoiceByName.argtypes = [C.c_char_p]
    if lib.espeak_SetVoiceByName(b'pt-br') != 0:
        raise RuntimeError('Voz pt-BR obrigatória não disponível')
    lib.espeak_SetParameter(1, 165, 0)
    chunks = []
    callback_type = C.CFUNCTYPE(C.c_int, C.POINTER(C.c_short), C.c_int, C.c_void_p)

    @callback_type
    def callback(samples, count, events):
        if samples and count:
            chunks.append(C.string_at(samples, count * 2))
        return 0

    lib.espeak_SetSynthCallback.argtypes = [callback_type]
    lib.espeak_SetSynthCallback(callback)
    lib.espeak_Synth.argtypes = [C.c_void_p, C.c_size_t, C.c_uint, C.c_int, C.c_uint, C.c_uint, C.c_void_p, C.c_void_p]
    data = text.encode('utf-8') + b'\0'
    result = lib.espeak_Synth(data, len(data), 0, 1, 0, 1, None, None)
    lib.espeak_Synchronize()
    lib.espeak_Terminate()
    if result or not chunks:
        raise RuntimeError('TTS não produziu áudio')
    with wave.open(str(output), 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(rate)
        stream.writeframes(b''.join(chunks))
    return {'provider': 'espeak-ng', 'voice': 'pt-br', 'language': 'pt-BR',
            'voice_manifest': 'Portuguese (Brazil)', 'human_accent_review': 'pending'}

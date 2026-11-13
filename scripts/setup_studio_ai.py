"""Explicit one-time download of the open faster-whisper pt-capable model."""
from attstudio.runtime import default_data_dir

def main():
    target=default_data_dir()/'models'/'faster-whisper-small';target.parent.mkdir(parents=True,exist_ok=True)
    if target.is_dir() and any(target.iterdir()):
        print(f'Modelo já instalado: {target}');return
    print('Baixando Systran/faster-whisper-small. Esta etapa pode levar alguns minutos…')
    from huggingface_hub import snapshot_download
    snapshot_download(repo_id='Systran/faster-whisper-small',local_dir=target)
    print(f'IA local instalada em: {target}')

if __name__=='__main__':main()

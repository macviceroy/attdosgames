# Instalar e abrir no Windows 10/11 x64

Use a branch `feat/studio-local-editor`. O Studio é novo, mas `attgames` e
`attpublish` continuam disponíveis. Não há publicação no Studio.

## Pré-requisitos

Python **3.12**, uv, FFmpeg/FFprobe no PATH (build com **libx264, AAC, libass**),
Chrome ou Edge atualizado. Não precisa de Node, GPU, conta nem cartão no editor
principal. Node >=22 + Chrome só são necessários para HyperFrames opcional.

Instale pelos distribuidores oficiais ou pelo Windows Package Manager:

```powershell
winget install --id Python.Python.3.12 -e
winget install --id astral-sh.uv -e
winget install --id Gyan.FFmpeg -e
```

Reabra o PowerShell após a instalação e confira `py -3.12 --version`,
`uv --version`, `ffmpeg -version`, `ffprobe -version`. Os comandos acima usam a
versão disponível nesses distribuidores; FFmpeg não está embutido no repositório.
A build validada aqui foi 7.1.5/Linux. A instalação em Windows/AMD ainda requer
validação na máquina de destino; não foi simulada nem declarada aprovada.

```powershell
git clone --branch feat/studio-local-editor https://github.com/macviceroy/attdosgames.git
cd attdosgames
uv sync --locked
uv run --locked pytest -q
uv run --locked attstudio
```

O navegador abre em **http://127.0.0.1:8765**. Alternativamente:

```powershell
.\scripts\install-studio.ps1
.\scripts\start-studio.ps1
# Sem abrir navegador, porta diferente:
.\scripts\start-studio.ps1 -Port 8766 -NoBrowser
```

Se a política do PowerShell impedir scripts locais, utilize os comandos `uv`
acima; não é necessário alterar a política global.

## Primeiro Short

1. Confirme sua autorização e informe a origem/licença dos arquivos.
2. Importe MP4/MOV/MKV/WebM/AVI. WAV/MP3/FLAC/OGG para áudio, PNG/JPEG para capa.
3. Escolha duração e modelo. Ajuste início/fim/enquadramento dos clipes na timeline.
4. Importe narração aprovada, opcionalmente música/SRT. Pode criar trilhas
   instrumentais procedurais synthwave, eletrônica ou lo-fi no próprio Studio.
5. Salve e renderize. A prévia renderizada é o MP4 final. A prévia do original
   mostra apenas a mídia de entrada e está identificada como tal.
6. Baixe MP4, PNG/JPEG, SRT, roteiro, metadados, projeto e relatório.

A narração não é fabricada: VoiceLabs Alex requer acesso oficial autenticado.
Arquivos sem voz são permitidos para edição de gameplay; QC não aprova sotaque.
Título/descrição/hashtags são editáveis; a estrutura de roteiro local não faz
pesquisa de notícias. Links públicos de vídeos não são baixados.

## Variações

Na aba Variações, selecione um vídeo da biblioteca e a duração por candidato.
A análise usa PySceneDetect, mudanças visuais amostradas e RMS de áudio.
Mostra sugestões sem sobreposição; assista, ajuste início/fim e crie cada Short.
Silêncios não são removidos. Não há análise semântica nem previsão de viralização.

## Transcrição opcional, sem serviços pagos

```powershell
uv sync --locked --extra transcription
```

Baixe conscientemente um modelo compatível faster-whisper e confira a licença.
Exemplo pequeno usado no teste (MIT; **não recomendado como garantia de precisão**):

```powershell
uv run --extra transcription python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-tiny', revision='d90ca5fe260221311c53c58e660288d3deb8d356', local_dir='models/whisper-tiny', token=False)"
$env:ATT_WHISPER_MODEL = (Resolve-Path .\models\whisper-tiny).Path
uv run --extra transcription attstudio
```

O primeiro download exige internet, não cartão. Depois, o adaptador usa apenas
arquivos locais, CPU/int8 e `language='pt'`. Whisper não identifica pt-BR versus
pt-PT. O modelo tiny errou a transcrição da amostra sintética testada; revise
palavras e timestamps ou importe um SRT revisado. Modelos maiores podem melhorar
precisão com maior consumo de RAM/tempo. Não há alinhamento forçado WhisperX.

## Armazenamento e limites

`studio-data/` guarda uploads, SQLite, revisões, jobs e exports. Para mover:

```powershell
$env:ATT_STUDIO_DIR = 'D:\ATT Studio\projetos'
uv run --locked attstudio
```

Use disco local, uma instância por diretório, um worker Uvicorn. Não exponha a
porta na internet/rede. O launcher limita a loopback e a API bloqueia clientes
remotos, hosts e origens não permitidas. Não é um servidor multiusuário.

Uploads até512 MiB/4h, montagem até180s/60clipes, até8jobs pendentes e2workers.
Vídeo longo pode levar vários minutos. Cancelar sinaliza o processo; se não
responder, encerra sua árvore. Em reinício, jobs incompletos ficam `interrupted`,
para retentativa explícita. Encerramento abrupto do sistema pode deixar arquivos
parciais, nunca disponibilizados como concluídos; Retentar remove essa tentativa.

Fontes disponíveis dependem dos arquivos licenciados em `brand/`. DejaVu vem
incluída. Bebas Neue/Montserrat só aparecem após arquivo TTF e sidecar
`.LICENSE.txt` correspondente. Nenhuma fonte é baixada automaticamente.

AMD: botão **Verificar AMD AMF** faz codificação real em1080×1920. Se falhar,
selecione CPU. O simples nome do encoder no FFmpeg não prova que a GPU funciona.
A exportação AMD também testa novamente e falha explicitamente se indisponível.

Os comandos antigos de demo eSpeak ainda existem e conservam suas limitações
Unix. O Studio não chama essa voz nem o worker antigo.

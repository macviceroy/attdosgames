# Dependências e direitos

- Arte procedural das cenas e capas: original desta implementação, CC0-1.0.
  Nenhum arquivo de gameplay ou trailer está incluído.
- DejaVu Sans Bold: licença Bitstream Vera/DejaVu completa distribuída em
  `brand/DejaVu-LICENSE.txt`. Não é CC0; manter aviso ao redistribuir a fonte.
- eSpeak NG é um projeto GPL-3.0-or-later. O pacote `espeakng-loader` baixa pelo
  gerenciador de dependências a biblioteca e dados; não incluímos a instalação
  `.venv` no pacote-fonte. Consulte https://github.com/espeak-ng/espeak-ng e os
  termos da versão efetivamente instalada antes de redistribuir um aplicativo
  que incorpore essa biblioteca. A licença do sintetizador não deve ser confundida
  com licença de cenas de terceiros ou com autorização para usar marcas.
- FFmpeg: depende da configuração do binário do sistema; libx264 normalmente
  implica build GPL. Não redistribuímos binários FFmpeg no pacote-fonte.
- FastAPI, Uvicorn, Pillow e dependências transitivas mantêm licenças próprias
  disponíveis nos pacotes fixados pelo lock. Não substituir licenças de terceiros
  por CC0 da arte gerada.
- yt-dlp é distribuído sob Unlicense. É usado somente para ingestão declarada
  como autorizada, sem cookies, playlists ou bypass de DRM. A licença do programa
  não concede direitos sobre o vídeo nem substitui os termos das plataformas.
- faster-whisper é opcional e MIT; o modelo Systran/faster-whisper-small é
  baixado somente pelo comando explícito `instalar-ia-local.cmd`. Confira o
  cartão/licença da versão do modelo antes de redistribuí-lo; modelos não entram
  no Git.

A biblioteca de demonstração é somente o conjunto procedural descrito no relatório.
Qualquer mídia adicionada depois exige verificação documental separada.

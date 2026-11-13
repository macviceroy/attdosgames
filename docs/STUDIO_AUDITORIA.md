# Auditoria anterior à implementação — 13/11/2026

Base: `b2318582529033f70c5a16ee7ccc576f64ebf61c`, branch de desenvolvimento
`feat/studio-local-editor`. Árvore completa consultada no GitHub; clone separado.

- Python 3.12, FastAPI, Pillow, FFmpeg/FFprobe, SQLite, uv.lock. Sem frontend,
  Node, HTML ou CSS na base. Não é possível localizar o site das imagens neste
  repositório. As imagens orientam o novo módulo, não comprovam código existente.
- `attgames`: CLI/API síncrona, worker separado, arte procedural e narração eSpeak
  pt-br. MP4/SRT/capa/relatório reais; roteiro é demonstração, sem pesquisa factual.
- `attpublish`: preparação local, simulador, SDK YouTube sem rede, idempotência,
  URLs HMAC temporárias. Publicação real bloqueada. Preservar integralmente.
- SQLite de produção guarda jobs/eventos; publicação tem banco separado. Diretório
  `data/` antigo já está versionado, incluindo um banco e intermediários. Não
  acrescentar bancos/estado operacional nem remover artefatos históricos nesta entrega.
- QC existente: duração, codecs, decodificação, áudio, hashes, legendas por frase.
  Não comprova sotaque, fatos, licença de uploads nem qualidade audiovisual.
- Windows não foi validado: timeout usa `os.killpg`, voz depende da biblioteca
  eSpeak; fontes dependem de caminhos. Studio deve evitar chamar esse pipeline
  de demonstração e usar subprocessos portáveis. Preservar testes existentes.
- Fontes: DejaVu licenciada em `brand/`; Bebas/Montserrat opcionais com sidecars.
- Nenhuma credencial VoiceLabs/Metricool disponível; não inferir autenticação do
  ChatGPT. Nova narração será importada; não haverá fallback para eSpeak.

Baseline executado antes das alterações: **60 passed**, 12,85 s, Linux/Python3.12.
Uma depreciação AnyIO/Starlette. Não houve publicação.

Arquitetura escolhida: `attstudio` acrescenta projeto versionado em SQLite,
frontend estático local, fila de subprocessos, importação validada, análise CPU,
composição FFmpeg e QC. Reutiliza fonte e helpers do motor. Nenhum segundo motor
(MoviePy/Editly/Remotion) para a mesma exportação.

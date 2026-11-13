# ATT DOS GAMES Studio — editor local

Evolução na branch `feat/studio-local-editor`: importação real, editor web,
Neon/Arcade/Cinema, cortes e reenquadramento, mixagem, SRT/ASS, capas, análise
local de cenas e exportação1080×1920. Publicação continua bloqueada.

No Windows, dê duplo clique em `iniciar-studio.cmd`. Ele preserva o modelo que
abre o Studio por CMD no navegador e instala somente dependências reproduzíveis.

```powershell
.\iniciar-studio.cmd
# uma vez, para roteiro/legendas automáticas locais:
.\instalar-ia-local.cmd
```

Também é possível iniciar manualmente com `uv sync --locked` e
`uv run --locked attstudio`.

Abra http://127.0.0.1:8765. [Windows e uso](docs/STUDIO_WINDOWS.md) ·
[Executável e instalador Windows](docs/STUDIO_EXECUTAVEL_WINDOWS.md) ·
[Auditoria](docs/STUDIO_AUDITORIA.md) · [22 repositórios avaliados](docs/STUDIO_REPOSITORIOS.md) ·
[Arquitetura e pendências](docs/STUDIO_ARQUITETURA.md) ·
[Testes reais](docs/STUDIO_TESTES.md) · [Vídeos e capturas](examples/studio/) · [VoiceLabs e Work](docs/STUDIO_VOICELABS_WORK.md).

O Studio aceita arquivo local ou URL HTTPS autorizada de YouTube, Instagram e
TikTok. A importação usa yt-dlp sem cookies, playlist ou contorno de DRM; o
usuário precisa declarar os direitos e respeitar os termos da plataforma.
“Automatizar este Short” executa análise, trilha procedural, transcrição,
roteiro baseado na fala, legendas, capa e render. Sem o modelo local, a tela
indica exatamente quais etapas ficaram bloqueadas.

**Limites:** VoiceLabs foi testado pelo conector oficial, mas o Python local não
herda credenciais; portanto a voz Alex ainda exige o fluxo autorizado do Work ou
importação do áudio. ASR e roteiro exigem revisão humana; não há publicação automática.
O frontend da imagem original não estava no repositório. A nova interface foi
acrescentada preservando os módulos anteriores documentados abaixo.

---

# ATT DOS GAMES — Fase 1 executável

Pipeline local de demonstração: **gera de verdade** MP4 H.264/AAC 1080×1920,
30 fps, capa PNG, SRT, roteiro JSON, título, legenda com hashtags, relatório
com hashes/licenças e QC. CLI e FastAPI compartilham persistência SQLite.
Não produz notícias reais nesta fase e não publica. Arte é um skyline neon
procedural original, não gameplay de GTA VI. Não há download de vídeos/trailers.

## Executar

Requisitos: Linux x86-64, Python **3.12**, `uv`, FFmpeg/ffprobe com libx264,
zoompan e AAC. O sintetizador eSpeak NG vem no pacote espeakng-loader (sem chave).
Não é necessário instalar espeak no sistema. Windows/macOS não foram validados.

```bash
cd att-dos-games
uv sync --locked
uv run python -m attgames produzir --tema "Rumores e fontes oficiais" --duracao 35
# Copie o id retornado para os comandos abaixo:
uv run python -m attgames status --id ID
uv run python -m attgames revisar --id ID
uv run python -m attgames publicar --id ID --plataformas instagram,youtube
# O último comando retorna erro de bloqueio e não chama serviços externos.
uv run pytest -q
uv run uvicorn attgames.api:app --host 127.0.0.1 --port 8000
```

Dependências diretas fixadas e transitivas com hashes em `uv.lock`.
As dependências do sistema FFmpeg/fontes não são instaladas pelo uv; a fonte
fallback e sua licença estão incluídas. `.env.example` é documentação: exporte
variáveis no ambiente; o programa não lê `.env` automaticamente.

Baixe este projeto em **Code → Download ZIP** ou pelo
[link direto](https://github.com/macviceroy/attdosgames/archive/refs/heads/main.zip).
A demonstração de 35 s e todas as suas entradas estão em
`data/ddc55657196a4ac782048f0ba838e022/`: abra `final.mp4` e `capa.png`.
O ambiente virtual e os caches não são distribuídos: recrie-os com `uv sync --locked`.
Os MP4s desta exportação foram compactados com H.264 veryfast CRF23,
sem alterar resolução/duração; áudio copiado, hashes atualizados e QC reexecutado.
O ZIP anterior de 151,2 MB do ambiente não é este arquivo: o ZIP do GitHub
contém o projeto e a demonstração, sem o ambiente virtual e a renderização auxiliar
de validação de 10 s.
`ATT_DATA_DIR` muda a pasta dos jobs.
Duração aceita: 10–60 segundos inteiros; tema: 1–64 caracteres. Não há parser
de linguagem natural: nesta fase a intenção é passada pelos argumentos da CLI.

## API

Documentação interativa local: `http://127.0.0.1:8000/docs`.

```bash
curl -X POST http://127.0.0.1:8000/produzir \
  -H 'Content-Type: application/json' \
  -d '{"tema":"Rumores e fontes oficiais","duracao":35}'
curl http://127.0.0.1:8000/status/ID
curl -X POST http://127.0.0.1:8000/revisar/ID
curl -X POST http://127.0.0.1:8000/publicar/ID \
  -H 'Content-Type: application/json' \
  -d '{"plataformas":"instagram,youtube"}'
```

Produzir é síncrono (pode levar minutos); o worker é um subprocesso isolado,
protegendo o estado global da biblioteca TTS entre requisições concorrentes.
Outro cliente pode consultar status enquanto renderiza. Esta API é local,
sem autenticação, quota ou fila distribuída: não expor à internet nesta fase.

## O que foi implementado

- Gancho inicial e roteiro original **de teste**, em português, com tema inserido.
- Voz explicitamente `pt-br` (manifesto `Portuguese (Brazil)`), nunca `pt-PT`.
- Cenas de aproximadamente 2,5 s, zoom progressivo, fades e textos incorporados
  às imagens, sincronizados por frase com a narração. SRT separado também incluído.
- Cada frase é sintetizada isoladamente; `atempo` ajusta sua duração, com pequeno
  respiro e padding. Não há alinhamento por palavra nem reconhecimento de fala.
- Paleta fornecida, capa e créditos @attdosgames. `brand/` não foi fornecida:
  usamos DejaVu Sans Bold licenciada. Veja `brand/README.md` para fontes opcionais.
- Música opcional não implementada; a demo não contém música.
- SQLite guarda jobs, eventos, estados, erros e reserva tabela de publicações.
  URLs remotas permanecem vazias porque nenhuma integração publica nesta fase.
- Chave única por tema normalizado/duração/versão e claim atômico impedem workers
  duplicados para o mesmo job. Repetir `produzir` devolve o job existente.
- Falhas não são retentadas cegamente. `produzir ... --retomar` (ou `retomar:true`
  na API) retenta somente `failed`/`qc_failed`, com teto de 3 tentativas totais.
  Artefatos anteriores são preservados em pasta de tentativa. Não há retries
  automáticos de rede, porque não há adaptadores de rede implementados.
- Um processo morto pode deixar `rendering` persistido: não há recuperação
  automática de leases. É necessário reconciliar o processo e estado antes de
  retomar; não alterar estado de worker ainda ativo.

## Qualidade e limites

O QC mede duração (tolerância 0,20 s), resolução/codecs, duração de áudio,
decodificação completa, presença de áudio audível, velocidade de fala até 2×,
intervalos dos cortes, continuidade, correspondência SRT/roteiro, hashes dos
arquivos e seleção explícita pt-BR. Direitos da arte procedural são registrados
como CC0-1.0; a fonte mantém licença própria. Isso não substitui análise jurídica.

O QC não identifica sotaque por análise acústica, não reconhece palavras,
não valida legibilidade por OCR e não comprova qualidade editorial. A verificação
de voz é de **configuração**; sotaque e pronúncia exigem escuta humana. O eSpeak
é robótico e serve para validar o fluxo; não é a voz comercial final.

O relatório tem `sources: []` intencionalmente: **não houve pesquisa de notícias**.
A mensagem de teste é incorporada ao vídeo. `publication_allowed` fica sempre
`false`, mesmo com QC técnico aprovado. `revisar` refaz o QC, não aprova publicação.
Modificar um arquivo coberto por hash invalida o QC. O manifesto local não é
assinado e não oferece resistência contra adulteração coordenada de arquivos.

## Próximas fases

Veja `INTEGRACOES.md` para credenciais, permissões, fontes oficiais consultadas,
limitações da investigação e critérios para publicação em aprovação e automática.
Nenhuma conexão externa ou credencial foi configurada no Codex para este projeto.



## Fase 3 — publicação em dry-run (novo)

Módulo separado `attpublish`: recebe MP4, PNG e metadados; valida arquivos reais,
prepara JPEG para Instagram e compila pedidos do YouTube pelo SDK oficial.
A autenticação, os IDs e as confirmações são **simulados**. Nenhum pedido é
enviado aos provedores; a publicação real é bloqueada mesmo com variáveis de
credenciais configuradas. O motor `attgames` e seus testes continuam preservados.

```bash
uv sync --locked
uv run attpublish dry-run --manifest examples/publication-dry-run.json
uv run uvicorn attpublish.api:app --host 127.0.0.1 --port 8001
uv run pytest -q
```

Documentação: [publicação e credenciais](docs/PUBLICACAO_FASE3.md),
[ChatGPT Work](docs/CHATGPT_WORK.md) e [resultado dos testes](docs/PHASE3_TEST_REPORT.md).
Não há adaptador Metricool nem herança de tokens do ChatGPT.

## Entrega temporária ao Work/agente externo

`attpublish.handoff` disponibiliza manifesto, MP4, PNG e JPEG por URLs assinadas,
expiráveis e revogáveis, sem publicar. Requer hospedagem HTTPS autorizada para
consumo externo. [Instruções Work/Metricool](docs/HANDOFF_WORK_METRICOOL.md).

# Fase 3 — integração offline de publicação

Implementado em `attpublish/`, independente de `attgames/`. O motor e os 17
testes originais são preservados. O comando antigo `attgames publicar` permanece
bloqueado. Não há transporte autenticado nem caminho de execução que publique:
esta entrega prepara pedidos oficiais e exercita contratos internos com fixtures.

## Executar

Python 3.12, FFmpeg/ffprobe e dependências fixadas pelo `uv.lock`:

```bash
uv sync --locked
uv run attpublish dry-run --manifest examples/publication-dry-run.json --output dry-run.json
uv run attpublish status --id ID_RETORNADO
uv run attpublish reconciliar --id ID_COM_SIMULATION_UNKNOWN
uv run attpublish publicar
# O último comando SEMPRE termina com live_disabled, exit 2.
uv run pytest -q
uv run uvicorn attpublish.api:app --host 127.0.0.1 --port 8001
```

Execute a partir da raiz do projeto. Caminhos no manifesto são relativos ao
processo, não ao arquivo JSON. O exemplo usa a demonstração já versionada no
repositório. Troque `video`, `cover`, `title`, `description` e `hashtags` para
seus arquivos locais. Não coloque tokens no manifesto. `made_for_kids: null`
significa classificação de audiência pendente; não inferimos uma decisão.

A autenticação é explicitamente `simulated: true`, com identidade `sim_*`,
permissões e expiração. Não existe consulta a conta, OAuth ou validade real.
Uma fixture expirada, sem timezone ou sem scopes necessários é rejeitada.
Campos extras como `access_token` são rejeitados; a API não ecoa seus valores.

`ATT_PUBLISH_DATA_DIR` seleciona o banco e arquivos preparados (padrão
`publication-data/`, ignorado pelo Git). Não é o SQLite do motor de produção.
`.env.example` não é carregado automaticamente; use variáveis de ambiente.

## Arquivos e preparação

Valida arquivos reais, extensão e conteúdo, MP4 com um vídeo H.264/yuv420p e um
áudio AAC, 1080×1920, 23–60 fps, duração 3–180,2 segundos (tolerância técnica de
200 ms), áudio mono/estéreo até 48 kHz, bitrate de vídeo até 25 Mbps e tamanho de
até 300 MB. Exige PNG 1080×1920 até 20 MB. Esses limites mais estritos são o
perfil deste projeto; não descrevem todos os formatos aceitos pelas plataformas.
A aceitação e classificação final em Reels/Shorts continuam dependentes da rede.

FFmpeg decodifica a entrada para detectar corrupção. Um MP4 derivado é remuxado
com `+faststart -use_editlist 0`, sem recodificar áudio ou vídeo; o original é
preservado. O PNG original é mantido, e um JPEG sRGB de até 8 MB é preparado
para Instagram. Alfa é composto sobre o preto da marca. Hashes verificam as
entradas e os derivados, incluindo reutilização e detecção de alterações.

Título: até 100 caracteres; descrição final do YouTube: até 5000 bytes UTF-8;
legenda completa do Instagram: até 2200 caracteres. Há limite conservador do
**produto** de cinco hashtags (não uma afirmação de limite universal da API).
As hashtags são normalizadas e incorporadas às descrições/legendas.

Não se trata de aprovação de sotaque, narrativa, direitos ou qualidade visual.
O módulo não pesquisa notícias, não certifica licenças e não converte uma
aprovação técnica do motor em autorização de publicar.

## Instagram Reels: capa e fluxo oficial

Rota escolhida: Instagram API com Instagram Login. Plano lógico:

1. `POST /{ig_user_id}/media`, com `media_type=REELS`, caption, `video_url` e `cover_url`.
2. `GET /{container_id}?fields=status_code`, aguardando `FINISHED`.
3. `POST /{ig_user_id}/media_publish`, com `creation_id`.
4. Consulta do media ID, tipo e permalink para confirmação futura.

O host da rota é `graph.instagram.com`; versão Graph deve ser escolhida da
lista suportada no app Meta antes de criar transporte real. Não foi inventada
uma versão vigente ou consultada uma conta real.

A referência consultada exige **JPEG**, até 8 MB, para a capa do Reel. `cover_url`
deve apontar a uma imagem que a Meta consiga buscar em servidor público.
O PNG de entrada é convertido localmente: um caminho local não serve de URL.
No plano, URLs são bindings pendentes, não endereços falsos de mídia hospedada.
Se a capa não estiver disponível, a alternativa documentada é `thumb_offset`
em milissegundos (0 = primeiro quadro); isso não utiliza o PNG personalizado.
`cover_url` tem precedência se ambos forem informados, por isso não enviamos ambos.
A hospedagem não foi criada e o fallback é somente descrito no plano nesta fase.

Referências oficiais consultadas em 10/11/2026:
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing
- https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/

## YouTube Shorts: miniatura e fallback

Não há endpoint separado para upload de Shorts. O adaptador usa os métodos
oficiais `videos.insert` (retomável, plano de privacidade `private`) e
`videos.list(part=processingDetails,status)` para confirmação de processamento.
A classificação como Short é da plataforma, não um campo que forçamos no upload.

**Resultado da consulta atual, não uma regra histórica:** a página oficial
`thumbnails.set` consultada em 10/11/2026 declara suporte a Shorts e determina
esperar `processingDetails.processingStatus=succeeded` antes de aplicar a capa.
O Help consultado informa canal verificado e upload manual no YouTube Studio
em computador, recomendando imagem 9:16. Não afirmamos que a API proíbe
miniaturas de Shorts, nem que a permissão está disponível para qualquer canal.
A referência do método consultada lista JPEG/PNG e limite de 50 MB; nossa
política de entrada PNG é mais conservadora (20 MB).

Com fixture `thumbnail_capability=available`, o plano inclui `thumbnails.set`
somente depois da consulta de processamento. Com `unknown`/`unavailable`, omite
a chamada e sinaliza miniatura automática da plataforma. O simulador também
exercita negação de permissão ao tentar aplicar a capa, preservando o upload
simulado e registrando o fallback. Não garante qual quadro o YouTube escolherá.
Uma opção manual é aplicar o PNG no Studio desktop quando a conta for elegível.
Não alteramos o MP4 para prometer uma capa específica.

`google-api-python-client==2.182.0` compila os pedidos usando discovery estático
embutido e um transporte que recusa HTTP. Não usa ADC nem tokens implícitos e
não chama `.execute()`. Isso testa os nomes/argumentos dos métodos do SDK;
não comprova aceitação pela API, permissões ou visibilidade real de miniatura.
As respostas do simulador são um contrato interno simplificado, não uma gravação
nem um emulador completo de todas as respostas JSON dos fornecedores.

Referências oficiais:
- https://developers.google.com/youtube/v3/docs/videos/insert
- https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol
- https://developers.google.com/youtube/v3/docs/thumbnails/set
- https://support.google.com/youtube/answer/72431?hl=en

URLs, horários HTTP e hashes das consultas estão em `phase3-documentation-checks.json`.
Limites e capacidades devem ser revalidados ao implementar transporte real.

## Idempotência, IDs e confirmação

O banco separado reserva atomicamente `(plataforma, conta simulada, hash do
vídeo de origem)`. Repetir o mesmo payload devolve IDs e eventos existentes,
sem simular outro upload. Alterar título/capa/metadados para o mesmo vídeo e
conta gera `duplicate_payload_conflict`, em vez de duplicar uma postagem.
A reserva de múltiplas plataformas é transacional: um conflito desfaz o lote.

Há claim atômico do simulador, eventos com data, persistência de IDs `sim_*` e
estados `prepared`, `simulating`, `simulated_confirmed`, `simulation_unknown`
e `simulation_failed`. Timeouts ou confirmação inconsistente não provocam
novo upload. `reconciliar` consulta somente a confirmação simulada, reutilizando
IDs já persistidos. Não reenvia mídia. Se não há ID ou se um processo morreu em
`simulating`, é necessária investigação; não existe recuperação automática de lease.

`simulated_confirmed` NÃO é publicação: sempre `published=false`,
`real_confirmation=false`, `remote_id=null`, `remote_url=null`. O próprio banco
impede gravar IDs/URLs reais nesta versão. Não existem URLs fictícias de posts.
Para integração real será necessária uma migração explícita e outro transporte,
com upload retomável, backoff limitado/Retry-After e reconciliação remota real.
Não há promessa universal de exactly-once em serviços externos.

## API e acesso

- `POST /dry-runs`: recebe o mesmo JSON do exemplo.
- `GET /dry-runs/{id}`: estado, plano, IDs simulados e eventos.
- `POST /dry-runs/{id}/reconcile`: reconciliação somente simulada.
- `POST /publish`: sempre HTTP 423 `live_disabled`.

No loopback, funciona sem chave para desenvolvimento. Definir
`ATT_PUBLISH_API_KEY` com pelo menos 32 caracteres exige o header
`Authorization: Bearer <chave>` inclusive no loopback. Requisições de clientes
não locais são bloqueadas sem configuração de chave. A chave autentica NOSSA
API, não as redes sociais. Não é uma implementação OAuth/MCP pronta para internet.
Não expor a API de caminhos locais diretamente a múltiplos usuários: uma ponte
remota deve mapear uploads autorizados para asset IDs em diretório controlado.

## O que falta para autenticação real

| Destino | Credenciais e permissões faltantes |
|---|---|
| YouTube | Projeto Google Cloud, YouTube Data API v3 habilitada, tela de consentimento OAuth, cliente desktop/web com redirect URI correta, autorização do dono do canal e refresh token seguro. Scopes usados pelo plano: `youtube.upload` e `youtube.readonly`, com os prefixos completos no exemplo. Confirmar verificação/elegibilidade para miniatura; quotas e políticas do projeto/canal. Implementar OAuth e transporte do SDK; não existem neste módulo. |
| Instagram Login | Conta profissional Business/Creator, Meta app configurado, app ID/secret, redirect URI, IG user ID e token do proprietário com `instagram_business_basic` e `instagram_business_content_publish`; revisão/acesso e verificação aplicáveis ao público do app. Versão suportada da Graph, hospedagem HTTPS de MP4/JPEG, consulta de limites e transporte de publicação. Não misturar os scopes do Facebook Login. |
| Metricool | Confirmação de plano Advanced/Custom e API habilitada, documentação oficial acessível, token/identificadores exigidos pelo contrato e conexões OAuth oficiais das redes na própria Metricool. A página oficial retornou HTTP 403; nenhum endpoint, SDK ou credencial foi presumido. Nenhum adaptador Metricool foi implementado. |

Não inserir tokens no chat, repositório, manifestos, relatórios ou logs. Usar
secret manager/variáveis no servidor e implementar renovação/revogação antes
de habilitar qualquer transporte. Nenhum token do plugin Metricool do ChatGPT
é herdado ou lido pelo processo Python.

Para ChatGPT Work, veja `CHATGPT_WORK.md`. Resultado dos testes executados:
`PHASE3_TEST_REPORT.md`.

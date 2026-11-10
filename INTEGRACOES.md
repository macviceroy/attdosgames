# Integrações pendentes e autorizações

Consulta técnica: 10/11/2026. Nenhuma credencial real foi encontrada, solicitada,
criada ou usada. Variáveis de `.env.example` são placeholders e não ativam
adaptadores. Configurar segredos no ambiente/secret manager, nunca no chat.

## Fase 2 — pesquisa, roteiro factual, voz e biblioteca

**Pesquisa:** implementar coletor com prioridade ao [Rockstar Newswire](https://www.rockstargames.com/newswire)
e páginas oficiais. A página respondeu HTTP 200, mas seu shell HTML não constitui
notícia validada. Cada item deverá guardar URL canônica, título, data publicada,
data de acesso, trecho que sustenta a alegação e classificação oficial/rumor.
Não inferir data de publicação da data de coleta. Não exige credencial para
páginas públicas; uma API de busca opcional exigirá chave e contrato do provedor
escolhido. Nenhum fornecedor de busca foi selecionado nesta fase.

**Roteiro:** o gerador da Fase 1 é um template original de teste, não um modelo
que pesquisa ou redige notícias. Um provedor de LLM é opcional na Fase 2 e ainda
não foi escolhido; se adotado, exigirá chave e revisão dos termos, além de
validação de cada afirmação contra as fontes coletadas.

**TTS de produção:** opção concreta Azure AI Speech, SDK oficial
`azure-cognitiveservices-speech`, recurso Speech com faturamento, região e
`AZURE_SPEECH_KEY` / `AZURE_SPEECH_REGION`; voz explicitamente
`pt-BR-FranciscaNeural` ou outra voz pt-BR retornada pelo catálogo. Confirmar
permissão de uso comercial no contrato vigente. Não é um adaptador implementado.
Alternativa: Google Cloud Text-to-Speech via SDK oficial `google-cloud-texttospeech`,
API habilitada, billing, Application Default Credentials/Workload Identity ou
arquivo de service account fora do repositório, autorização para invocar o serviço no projeto (confirmar o papel IAM vigente
na implementação), `language_code=pt-BR` e nome de voz
brasileira explícito. Fazer escuta humana antes de aprovar. Nunca fallback pt-PT.
A Fase 1 já funciona sem essas credenciais, com eSpeak NG offline.

**Mídia:** faltam os arquivos reais de identidade e respectivas permissões;
clipes próprios/autorizados e sua documentação. Fornecedor externo ainda não
escolhido: não há chave universal. Contratar acesso via API/licença que permita
uso comercial, recorte, edição e distribuição nas duas redes. Manifesto deve
registrar origem, autor, licença/contrato, comprovante, restrições, atribuição,
validade, território e direitos de trilha, imagem e marcas. A demo só utiliza
arte procedural original CC0 e fonte DejaVu com licença incluída. Nenhuma
licença de trailer da Rockstar foi presumida. Música permanece desligada até
existir arquivo e autorização que cubra ambas as plataformas.

## Fase 3 — publicação real com aprovação

### YouTube Data API

Documentação oficial consultada com HTTP 200:
- [videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)
- [Uploads retomáveis](https://developers.google.com/youtube/v3/guides/using_resumable_upload_protocol)

Faltam projeto Google Cloud com YouTube Data API v3 habilitada, configuração da
tela de consentimento OAuth, cliente OAuth (desktop para CLI ou web para serviço
com redirect URI exata), autorização do proprietário do canal e refresh token
armazenado com segurança. Escopo mínimo para upload:
`https://www.googleapis.com/auth/youtube.upload`. Usar bibliotecas oficiais
`google-api-python-client` e `google-auth-oauthlib`; uploads retomáveis com URI
de sessão persistida e consulta de progresso antes de repetir. Definir privacidade
explicitamente (iniciar em `private` para aprovação), audiência infantil e demais
metadados obrigatórios. Não depender de defaults de privacidade. Quotas,
consentimento/verificação e restrições devem ser revalidados para o projeto real.
Não existe endpoint separado "upload de Shorts": enviar o vídeo pelo upload
normal; a classificação como Short é da plataforma. A conta autorizada não está
conectada a este projeto.

### Instagram API

[Content Publishing, documentação oficial](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing)
respondeu HTTP 200 e descreve criação de container, consulta de status e
publicação. Esses passos ainda não estão implementados.

Rota preferida: Instagram Login. Faltam conta profissional (Business/Creator),
Meta app com Instagram API configurada, app ID/secret, redirect URI OAuth,
Instagram user ID e token autorizado. Permissões:
`instagram_business_basic` e `instagram_business_content_publish`.
Configurar acesso/revisão do app e requisitos de verificação aplicáveis ao uso
real; tokens de teste/desenvolvimento não substituem aprovação para usuários
externos. Para Instagram Login, não presumir necessidade de Facebook Page.

Se optar por Facebook Login, os requisitos são diferentes: conta profissional
ligada a Page, permissões `instagram_basic`, `instagram_content_publish` e
`pages_read_engagement`, além de permissões adicionais conforme o fluxo real
(por exemplo `pages_show_list` para seleção de páginas). Não misturar os dois
conjuntos de escopos. Confirmar a versão e requisitos no momento da implementação.

O fluxo documentado cria container com `media_type=REELS`, aguarda o processamento
e então publica. Faltam hospedagem HTTPS acessível à Meta para o arquivo (ou
implementação do upload retomável documentado), checagem de limites e tratamento
de expiração dos containers. Guardar o ID do container e consultar seu estado
antes de repetir `media_publish` em respostas ambíguas. Nunca usar navegador ou
senha para contornar a API.

### Metricool

A alternativa solicitada depende de plano **Advanced/Custom e habilitação de API**,
a confirmar na conta/contrato. Foram tentados o [portal oficial](https://metricool.com/api/)
e uma página de ajuda; ambos retornaram HTTP 403 neste ambiente. Portanto,
**não foi possível confirmar documentação, endpoints, escopos ou disponibilidade
por rede**. Não há adaptador nem endpoint inventado.

Faltam confirmação contratual, documentação oficial acessível fornecida pela
Metricool, token de API, IDs de usuário/marca (`userId`/`blogId`, se confirmados
pela documentação da conta) e conexão OAuth oficial das duas redes na Metricool.
`METRICOOL_*` são nomes locais propostos, não prova do contrato da API.
Validar suporte a Reels/Shorts, agendamento, capas, limites, idempotência e
consulta de status antes de implementar. Evitar publicar simultaneamente por
Metricool e por APIs diretas para o mesmo job/plataforma.

## Aprovação, retentativas e Fase 4

Antes da Fase 3: persistir snapshot imutável/hash de vídeo, capa, metadados e
licenças que o proprietário aprovar; vincular autorização ao hash e plataformas.
Aprovação antiga deve expirar se o conteúdo mudar. Implementar state machine de
publicações com chave única `(job_id, platform)`, IDs remotos/URLs, leases,
backoff limitado com jitter e `Retry-After`. Depois de timeout de operação remota,
reconciliar a sessão/container antes de tentar novamente; não existe garantia
universal de exactly-once em APIs externas. A tabela atual é apenas preparação,
não uma implementação desses adaptadores.

Fase 4 só após testes reais autorizados em modo privado/teste quando suportado,
verificação de duplicação/reinício/expiração de token e autorização explícita do
proprietário para o escopo automático. Não existe flag que burle esse processo.

`consulta-documentacao.json` registra URLs, horário da coleta e respostas da
consulta inicial. Esses links são documentação técnica, não fontes de notícias
do vídeo. A tentativa posterior de `https://metricool.com/api/` também resultou
em HTTP 403. Nenhum token deve constar desses relatórios.

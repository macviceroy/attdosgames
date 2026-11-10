# Entrega temporária ao Work e agente externo

O novo `attpublish.handoff` entrega arquivos e metadados. Não agenda, não publica,
não implementa OAuth de redes e não chama Metricool. O dry-run anterior permanece
intacto. Consumir um arquivo não constitui confirmação de publicação.

## Usar no executor Work

Na raiz do repositório, após `uv sync --locked`:

```bash
# Manter este diretório privado, persistente e fora do Git:
export ATT_HANDOFF_DATA_DIR=/caminho/privado/att-handoff
uv run uvicorn attpublish.handoff:app --host 127.0.0.1 --port 8002 --no-access-log
```

Configure um domínio HTTPS autorizado com proxy para esse servidor. Em outro
terminal, com a MESMA variável ATT_HANDOFF_DATA_DIR:

```bash
uv run python -m attpublish.handoff create \
  --manifest examples/publication-dry-run.json \
  --origin https://SEU-DOMINIO-AUTORIZADO --ttl 900
```

Edite o manifesto de exemplo para o MP4, PNG, título, descrição e hashtags do
job desejado. O formato é o mesmo do dry-run anterior; fixtures de autenticação
continuam sintéticas e não são incluídas no manifesto entregue. Não colocar
segredos no JSON. Caminhos são relativos ao processo. A resposta contém ID,
expiração Unix e `manifest_url`, sem alegar que a hospedagem funciona.

O agente externo faz GET dessa URL e recebe metadados e URLs de `video`, `cover`
(PNG) e `instagram_cover` (JPEG derivado), MIME types e SHA-256. Baixa os arquivos
e verifica os hashes. O MP4 é uma cópia remuxada pelo preparador existente; os
arquivos originais são preservados. Ele deve respeitar `publication_allowed=false`
e não chamar ferramentas de publicar/agendar.

Peça ao Work: “Crie a entrega temporária deste manifesto; forneça a manifest_url
somente ao agente autorizado para inspeção. Não publique nem agende.” O executor
precisa do código, arquivos e acesso ao diretório persistente. A criação ocorre
pela CLI confiável: não existe rota pública de criar entregas ou ler paths arbitrários.

## Repetir, renovar e revogar

Repetir os mesmos arquivos preparados, metadados e origem reutiliza ID, prazo e
URLs (TTL diferente não renova implicitamente). Concorrência usa reserva SQLite
transacional. Se a entrega expirou ou foi revogada, a criação falha até renovação
explícita com `--renew`. A renovação troca nonce e invalida as URLs anteriores,
mesmo que o novo prazo coincida. Para revogar imediatamente:

```bash
uv run python -m attpublish.handoff revoke --id ID
```

Assinaturas HMAC-SHA256 vinculam ID, recurso, nonce e prazo; TTL permitido é
60–3600 s. Uma assinatura do manifesto não autoriza baixar outro recurso.
Arquivos adulterados são recusados. Não há listagem de diretório nem download
de nomes fornecidos pelo cliente. Respostas usam no-store e no-referrer.

## Segurança e hospedagem pendentes

- URLs são capacidades bearer: qualquer pessoa com o link pode consumi-lo até
  expirar/revogar. Não enviar ao Git, screenshots públicos, analytics ou logs.
  O manifesto também contém links sensíveis. Use somente destinatário autorizado.
- O banco e a chave HMAC ficam no diretório privado (0700; chave/banco 0600).
  Compartilhar esse estado entre CLI e serviço. A chave NÃO é token Metricool.
  Fazer backup protegido; rotação global da chave invalida todos os links.
- Desabilitar access logs também no proxy/CDN e redigir query strings em logs
  de erro/observabilidade. Não colocar CDN cache diante das respostas. Respeitar
  Cache-Control; não aceitar cache de arquivos para manter revogação efetiva.
- Faltam domínio, DNS, certificado TLS, proxy, disco persistente autorizado,
  firewall e acesso do consumidor. Não foram criados nem testados aqui.
  Nunca expor diretamente HTTP/porta 8002 à internet; limitar upload/criação à CLI.
- Validar os bytes e MIME types a partir da rede do consumidor após hospedar.
  HTTPS no parâmetro não instala certificado nem comprova reachability.
- Downloads já concluídos não podem ser apagados pela revogação. Um stream já
  autorizado pode terminar após expirar; novas requisições são recusadas.
  Prazo deve cobrir o download inteiro e retries autorizados do consumidor.
- Não há coleta automática de expirados: remover bundles/assets não utilizados
  segundo política de retenção, após assegurar que nenhuma entrega ativa os usa.
- Não há garantia contra um administrador que altere banco/chave/arquivos; o
  diretório deve ficar sob controle exclusivo do serviço. Não é um cofre multiusuário.

Armazenamento externo autorizado (S3/GCS ou equivalente) pode substituir o
serviço depois com URLs GET pré-assinadas, bucket privado e TTL curto. Esse
adaptador não está implementado e nenhuma conta de armazenamento foi conectada.

## Metricool conectado ao ChatGPT

A conexão no ChatGPT não fornece suas credenciais ao Python. Este módulo não
busca nem solicita esses tokens e não inventa endpoints Metricool.

No ChatGPT, selecione o plugin disponível e confira suas ferramentas reais:
se houver ferramenta autorizada de importar/inspecionar mídia por URL, ofereça
somente os links necessários e metadados, dentro do prazo. Se só existir publicar
ou agendar, NÃO a use nesta fase. Aceitação de URL, PNG/JPEG, preview/rascunho,
limites e contas acessíveis dependem das ferramentas e do contrato da conexão.
Não foram verificados nesta entrega. Não prometa importação onde não há ferramenta.

Se o plugin não conseguir acessar URLs ou oferecer somente publicação, o agente
externo pode consumir o manifesto para inspeção e parar. A integração Metricool
fica pendente até existir operação adequada e autorizada. Nenhuma etapa deve
publicar automaticamente porque conseguiu baixar o arquivo.

Uma ponte MCP para chamar a CLI/ler entregas pode ser adicionada conforme
CHATGPT_WORK.md; REST e CLI não são um endpoint MCP. Não instalamos plugin,
ponte, hospedagem nem conexão nesta sessão.

## Teste executado e limites

Teste E2E: cliente externo simulado requisita manifesto via HTTP/ASGI, consome
MP4, PNG e JPEG reais preparados por FFmpeg/Pillow, verifica MIME, hashes e
metadados. Há testes de assinatura alterada/troca de recurso, expiração, revogação,
renovação que invalida links antigos, integridade, origem/TTL e emissão concorrente.

É transporte ASGI com URL de teste https://delivery.example, NÃO handshake TLS
real nem domínio hospedado. Nenhuma chamada ao Metricool ou rede social.
Todos os testes anteriores, inclusive bloqueios de publicação, continuam na suíte.
Consultar HANDOFF_TEST_REPORT.md para o resultado desta execução.

# Conectar ao ChatGPT Work

Esta entrega fornece CLI e REST local, não instala um plugin, não cria conexão
OAuth e não disponibiliza endpoint MCP. Conexão GitHub permite obter arquivos;
não implica credenciais de YouTube, Meta ou Metricool dentro do executor.

## Work com ambiente de execução

1. Selecione/clonar `macviceroy/attdosgames` no ambiente Work e habilite Python
   3.12 e FFmpeg. Execute `uv sync --locked` na raiz.
2. Coloque os arquivos MP4/PNG em diretório acessível ao executor. Prepare um
   manifesto como `examples/publication-dry-run.json`, somente com metadados,
   caminhos e identidades simuladas `sim_*`.
3. Peça ao agente: “Execute `uv run attpublish dry-run --manifest CAMINHO`,
   reporte os IDs e pendências; não publique”. `AGENTS.md` documenta o bloqueio.
4. Use `attpublish status --id ID` para inspeção e `reconciliar` apenas quando
   `simulation_unknown`. Guarde o JSON no ambiente. Nenhuma chave de rede social
   é necessária para esse fluxo; o agente executa a CLI, não o plugin Metricool.

Este é o caminho utilizável hoje quando o Work oferece um executor com o projeto.
Os paths `/workspace` desta sessão não são automaticamente os do seu computador
nem de outro ambiente Work. O script não cria links públicos de mídia.

## Work/ChatGPT por plugin com ferramentas MCP

Se o agente não tiver executor, será necessária uma **ponte MCP adicional**, não
implementada aqui. A REST API `/dry-runs` não fala o protocolo MCP e não deve ser
cadastrada como se fosse `/mcp`.

1. Implemente a ponte com o SDK oficial MCP/Apps SDK. Exponha somente ferramentas
   `att_prepare_dry_run`, `att_dry_run_status` e `att_reconcile_simulation`, que
   chamem os serviços REST correspondentes. Use schemas, descrições e anotações
   corretas: preparar/reconciliar escrevem estado local, mesmo sem posts reais.
   Não exponha ferramenta de publicação real nesta fase.
2. Hospede em HTTPS com streamable HTTP em `/mcp`, ou use Secure MCP Tunnel
   quando disponível na conta/workspace. Faça autenticação/discovery adequados
   ao MCP e políticas do workspace. A ponte guarda sua chave de acesso ao backend
   em secret manager; nunca pede que o modelo inclua tokens de provedores.
3. A ponte deve receber uploads autorizados e mapear asset IDs a arquivos sob uma
   raiz controlada; não aceitar caminhos arbitrários fornecidos por usuários remotos.
   O backend deve ficar privado, com `ATT_PUBLISH_API_KEY` e isolamento por usuário.
4. Valide com MCP Inspector. Na interface documentada consultada: **ChatGPT Plugins
   → + → Add custom MCP server**, selecione HTTPS ou Tunnel, configure autenticação
   e crie como plugin, respeitando permissões do workspace. A disponibilidade e os
   nomes podem variar com plano/interface. Inicie nova conversa e selecione via `@`.
5. Teste seleção da ferramenta, schemas, erros, estados e confirmação simulada.
   Essa conexão NÃO foi criada nem testada nesta entrega: falta a ponte,
   hospedagem/túnel, autenticação e autorização administrativa quando aplicável.

Referência oficial consultada com HTTP 200 em 10/11/2026:
https://developers.openai.com/apps-sdk/deploy/connect-chatgpt/

Nenhuma dessas conexões transporta automaticamente a autorização de um plugin
Metricool para código local. A publicação real continua desabilitada mesmo que
o operador configure variáveis contendo credenciais.

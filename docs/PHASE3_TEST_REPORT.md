# Fase 3 — relatório simples

Data: 10/11/2026. Resultado: **APROVADO para dry-run offline**.
Nenhuma publicação real foi realizada. Não é validação audiovisual ou editorial.

| Verificação | Resultado | Evidência |
|---|---|---|
| Motor existente e testes preservados | Aprovado | SHA-256 dos 12 arquivos Python originais (motor + testes) inalterados. Os 17 testes anteriores passaram. |
| Dependências e empacotamento | Aprovado | `uv sync --locked`; build de wheel/sdist 0.2.0 com os dois módulos. SDK oficial Google fixado no lock. |
| Arquivos reais e preparação | Aprovado | CLI processou o MP4 de 20 segundos do teste anterior e capa PNG. FFmpeg decodificou/remuxou e Pillow preparou JPEG sRGB. Originais preservados. |
| Pedidos oficiais YouTube | Aprovado offline | SDK oficial compilou `videos.insert`, `videos.list` e `thumbnails.set`, com discovery estático e transporte HTTP desabilitado. Nenhum `.execute()`. |
| Instagram | Aprovado offline | Plano REELS com cover_url para JPEG, processamento FINISHED, criação e confirmação com IDs sim_*. Não houve hospedagem, OAuth ou Graph API real. |
| Capas de Shorts | Aprovado offline | Casos elegível, indisponível, desconhecido, processamento pendente e negação de permissão simulada; fallback explícito para miniatura da plataforma. |
| Idempotência e estados | Aprovado | Repetição CLI/API retornou os mesmos IDs; testes de reserva concorrente, conflito transacional e reconciliação sem repetir upload passaram. |
| API local | Aprovado | HTTP real para dry-run e status; fixtures inválidas, autenticação da API e não ecoar tokens também testados. |
| Bloqueio de envio real | Aprovado | CLI `live_disabled`, exit 2; API HTTP 423. strace de CLI/subprocessos e servidor sem chamadas IP externas de saída. IDs/URLs reais null. |
| Suíte completa | Aprovado | **54 passaram**: 17 anteriores + 37 novos. Um aviso de depreciação Starlette/AnyIO; nenhuma falha. |

## O que ainda depende de autenticação/infraestrutura

- YouTube: consentimento OAuth real, proprietário do canal, upload/readonly,
  refresh seguro, capacidade de miniaturas, quotas, processamento e confirmação
  reais. Transporte autenticado não foi implementado nem testado.
- Instagram: app Meta, conta profissional, permissões e token reais, versão
  Graph, hospedagem HTTPS de MP4/JPEG, limites, aceitação e permalink real.
- Metricool: plano/API habilitada, documentação acessível e credenciais próprias.
  Consulta oficial retornou 403; não há adaptador nem herança de tokens do ChatGPT.
- ChatGPT Work: CLI utilizável no executor com o projeto. Ponte MCP, hospedagem
  ou Secure MCP Tunnel, autenticação e instalação como plugin não foram criados.

Credenciais/permissões: `PUBLICACAO_FASE3.md`. Como conectar: `CHATGPT_WORK.md`.
Evidência da execução: `phase3-runtime-evidence.json` e traces de rede anexos.
Fontes e horários: `phase3-documentation-checks.json`.

## Limites explícitos

Autenticação, IDs e confirmações são fixtures. `simulated_confirmed` não equivale
a publicação, nem prova que a rede aceitará o payload. O transporte real está
ausente e o método live bloqueado. Faltam aprovação editorial/de direitos,
OAuth real, recuperação de leases e integração remota para habilitar envio.

A revisão de segredos desta entrega verifica o conjunto de arquivos enviado,
com whitelist de caminhos e padrões de tokens/chaves, além da revisão dos
campos/erros. Não é garantia universal de ausência de qualquer segredo possível.

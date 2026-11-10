# Relatório da entrega temporária — 10/11/2026

Resultado: **60 testes passaram**, sem falhas; um aviso de depreciação
Starlette/AnyIO já existente. São os 54 testes anteriores e seis novos testes.

| Item | Resultado real |
|---|---|
| Cliente externo simulado E2E | Manifesto e três arquivos consumidos via HTTP/ASGI; metadados, MIME e SHA-256 conferidos |
| Idempotência | Mesma entrega/URLs ao repetir; emissão concorrente não duplica o bundle |
| Segurança dos links | Assinatura modificada e uso em outro recurso recusados |
| Ciclo de vida | Expiração e revogação recusam novas requisições; renovação invalida links antigos |
| Integridade | Arquivo adulterado não é entregue |
| Configuração | Origem sem HTTPS, credenciais na URL e TTL inválido recusados |
| Produção/publicação | Motor e módulos dry-run anteriores não alterados; bloqueios testados na suíte |
| Segredos | Revisão do conjunto textual enviado; sem chave HMAC, URLs assinadas, tokens, banco ou arquivos operacionais versionados |

Não houve OAuth direto, publicação, chamadas Metricool, hospedagem externa ou
handshake TLS real. O cliente E2E é simulado, com transporte ASGI. Não houve
verificação audiovisual/editorial. A importação por Metricool permanece pendente
da capacidade real da ferramenta autorizada e da hospedagem HTTPS.

Comando executado: `UV_CACHE_DIR=/workspace/work/uv uv run pytest -q`.
Reproduzir o E2E: `uv run pytest tests_publication/test_handoff.py -q`.
Configuração e instruções: [HANDOFF_WORK_METRICOOL.md](HANDOFF_WORK_METRICOOL.md).

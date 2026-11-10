# Validação executada

- 17 testes automatizados passaram (`uv run pytest -q`). Um aviso de depreciação
  da integração Starlette/AnyIO não afetou a execução.
- Build real de sdist e wheel concluído; fonte e licença presentes no wheel.
- Renderizações reais de 35 segundos e de 10 segundos concluídas pelo worker.
- Demo 35 s: H.264/AAC, 1080×1920, 30 fps; QC técnico aprovado; publicação bloqueada.
- API Uvicorn testada por HTTP: status, produção idempotente de job existente,
  documentação e tentativa de publicação com resposta 409.
- Alteração controlada no SRT real invalidou integridade e sincronização; após
  restauração byte a byte, o QC técnico voltou a aprovar.
- Capa inspecionada visualmente. Nenhuma aprovação humana de sotaque ou notícia.
- Nenhuma API de publicação foi chamada; nenhum post ou conexão OAuth foi criado.

Os testes unitários usam armazenamento temporário. Os testes HTTP e a inspeção
real dos artefatos foram executados adicionalmente neste ambiente. Isso não
constitui validação de produção ou de integrações futuras.

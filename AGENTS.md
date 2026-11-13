# ATT DOS GAMES
Python 3.12; executar `uv sync --locked` e `uv run pytest`.
Fase 1 é offline e não publica. Nunca remover bloqueios para contornar QC.
Nenhum trailer ou vídeo público implica licença comercial. Verificar proveniência,
termo, validade, território, atribuição e direitos sobre música, imagem e marcas.
Não adicionar segredos ou tokens a logs, relatórios ou ao repositório.
Obrigatório pt-BR explícito; nunca usar pt-PT como fallback.
Preservar idempotência transacional. Publicação de estado remoto desconhecido
exige reconciliação antes de nova tentativa; nunca repetir cegamente upload/post.
Não criar endpoints de fornecedores por suposição; consultar documentação oficial.

# Fase 3 de integração
`attpublish/` é separado do motor e permite somente dry-run offline.
Use `uv run attpublish dry-run --manifest examples/publication-dry-run.json`.
Nunca substituir identidades sim_* por tokens, nem tratar simulated_confirmed
como publicação. O CLI/API antigo de produção continua bloqueado.
A API REST nova não é um endpoint MCP; docs/CHATGPT_WORK.md explica a ponte pendente.

# Studio local
`attstudio/` e `scripts/studio_e2e.py` são a evolução do editor. Leia
`docs/STUDIO_ARQUITETURA.md`, `docs/STUDIO_TESTES.md` e
`docs/STUDIO_CONTINUAR.md` antes de retomar. Não substituir a voz aprovada por
eSpeak: Studio só importa áudio; transcrição não comprova sotaque nem exatidão.
`uv sync --locked` instala o editor; transcrição é extra opcional. Manter
`attgames/`, `attpublish/` e seus testes intactos. Nunca versionar studio-data,
modelos, tokens, node_modules ou bancos novos.

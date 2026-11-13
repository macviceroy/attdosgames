# Arquitetura e limites do Studio

```
Navegador (HTML/CSS/JS local, sem CDN)
       │ JSON / upload binário / Range MP4
FastAPI attstudio.api ── SQLite (assets, projects, revisions, jobs, events)
       │ fila limitada (2 subprocessos)
       ├─ análise: PySceneDetect + OpenCV + RMS
       ├─ transcrição opcional: faster-whisper CPU / modelo local
       └─ render: representação Project → FFmpeg → QC → artefatos
                 ├─ Pillow: títulos e capas
                 ├─ ASS/libass: legendas
                 └─ audio: volume / sidechaincompress / limiter
```

`attgames` e `attpublish` não foram substituídos. Studio reutiliza fontes/helper
de timestamp do motor e mantém FFmpeg como compositor principal. HyperFrames
opcional produz um asset MP4 a partir de template HTML/CSS confiável; depois
entra na mesma timeline. Não há dois motores concorrentes para montar o Short.

`Project` (Pydantic, extra=forbid) é o contrato de exportação, histórico e edição:
clipes com asset IDs e intervalos, foco X/zoom, narração/música e volumes, cues
com tempos, estilo, fonte, capa, metadata e encoder. Salvar usa controle otimista
de revisão; alterações concorrentes retornam409. Desfazer/refazer é local ao
rascunho; revisões salvas persistem. A prévia final é o mesmo arquivo exportado;
não há preview ao vivo de filtros enquanto se arrasta um controle.

Workers fazem claim SQLite. A chave inclui o projeto inteiro, ID e versão do
renderer; repetir parâmetros devolve o job, sem render duplicado. Falhas não são
retentadas automaticamente. Handoff/publicação têm idempotência independente,
preservada. Studio não conhece tokens nem importa adaptadores sociais.

Segurança: IDs em vez de caminhos arbitrários, listas permitidas de extensão e
artefatos, ffprobe real, limites, verificação SHA256, protocolos FFmpeg restritos,
subprocessos sem shell, ASS sem comandos do usuário, títulos via Pillow,
HTML via textContent, CSP e origem/cabeçalho de mutação. O módulo motion aceita
somente texto escapado e template do pacote. Não renderize HTML de terceiros.

## O que ainda não está pronto

- Validação prática em Windows10/11 e AMD Radeon; testes feitos em Linux/CPU.
- VoiceLabs Alex foi testado pelo conector oficial desta sessão. O adaptador MCP
  aceita sessão autenticada fornecida por um host; a UI exporta pedido para o Work.
  Autenticação TTS direta no Python local e revisão auditiva continuam pendentes.
  Não há herança de tokens do ChatGPT. Veja STUDIO_VOICELABS_WORK.md.
- Sem pesquisa factual, LLM semântico local, agentes gerais, seleção por eventos
  de gameplay, reconhecimento de rostos ou promessa de viralização.
- Transcrição automática exata não garantida. Tiny errou a amostra; alinhamento
  WhisperX/diarização adiado. Legendas/SRT devem ser revisados contra a fala.
- Histórico não é editor multipista completo: um título inicial, até oito camadas de texto temporizadas, legendas,
  clipes sequenciais e três fontes de áudio; sem drag-and-drop multipista,
  keyframes arbitrários, transições xfade com sobreposição ou ajuste de velocidade.
- Música procedural é simples; não é catálogo comercial nem trilha profissional
  aprovada. BPM/beat markers são registrados, mas cortes automáticos por batidas
  ainda não foram integrados.
- HyperFrames é CLI opcional; seu template é um título/intro, sem editor HTML livre
  no navegador. Exportação com alpha e integração como overlay avançado pendentes.
- Direitos de upload são declarações do usuário registradas com hash, não
  comprovação documental automática. QC técnico não prova qualidade audiovisual.
- ZIP de entrega implementado, sem entradas/logs/bancos; faltam quotas por usuário,
  criptografia de disco ou serviço público hospedado. Apagar projetos/GC de assets
  órfãos não possui interface; backups e manutenção do diretório são locais.
- Nenhuma rede social recebe conteúdo. Integração Work/Metricool anterior continua
  em entrega/dry-run; não foi conectada nesta evolução.

Após o checkpoint inicial: capas independentes e finais usam o mesmo gerador;
revisão por pixel confirmou intervalos das camadas. Lock por worker impede
retentativa de sobrescrever um processo sobrevivente ao reinício do servidor.

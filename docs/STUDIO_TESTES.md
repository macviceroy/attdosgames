# Testes reais — 13/11/2026

Linux x64, Python3.12.14, FFmpeg7.1.5, CPU. Windows e AMD não disponíveis.

| Etapa | Resultado | Evidência |
|---|---|---|
| Baseline anterior | Aprovado | 60 testes antes da alteração |
| Regressão + novos testes | Aprovado: execução final 79 testes aprovados na execução final | 73 testes, incluindo importação, Range, CSRF/host, revisões, hashes, idempotência, música, cancelamento e guardas |
| MP4 real e miniatura | Aprovado | Fixture original de36s,640×360, thumbnail200/Range206 |
| Neon, Arcade, Cinema | Aprovado técnico | Três MP4s6s1080×1920H.264/AAC; cortes, zoom, fades, título, ASS,3fontes de áudio, ducking, capas e metadados |
| Variações | Aprovado técnico | Análise real36s; três segmentos distintos10s exportados |
| Integridade/idempotência | Aprovado | Downloads SHA256 conferidos; render repetido reutiliza ID |
| Navegador | Aprovado | Chromium do sistema: upload, salvar, desfazer, exportar, tocar MP4,3candidatos, ajustar início; mobile sem overflow; zero pageerrors |
| HyperFrames | Aprovado geração | CLI opcional gerou MP4 real3s/90frames1080×1920; importação + concatenação FFmpeg + música procedural também aprovadas |
| faster-whisper | Execução aprovada, precisão reprovada | CPU int8/timestamps reais; modelo tiny interpretou incorretamente áudio sintético legado. Não gerar legenda final sem revisão |
| Publicação | Bloqueada como esperado | HTTP423, módulos anteriores preservados |
| Voz Alex | Geração oficial testada | Quatro falas pelo conector; não é autenticação automática do Python |
| Sotaque / qualidade editorial | Não aprovado | Sem revisão auditiva humana |

Evidências JSON em `studio-evidence/`; MP4s/capas em `examples/studio/`.
Mídia de E2E: padrões visuais e sinais de áudio procedurais originais CC0, sem
imagens do GTA, música comercial ou narração humana. A trilha que ocupa o slot
"narração" é um sinal de teste: comprova mixagem, não qualidade de fala.
A amostra antiga eSpeak foi usada exclusivamente para regressão ASR; não foi
adotada como voz do Studio nem substituiu VoiceLabs.

Erros reais encontrados e tratados:
- PyAV19.0.2 removeu `metadata_errors`, quebrando faster-whisper1.1.1;
  fixado em14.2.0 e inferência reexecutada.
- Chromium empacotado do Playwright não possuía H.264/AAC; confirmado com
  `canPlayType` vazio e `DEMUXER_ERROR_NO_SUPPORTED_STREAMS`. MP4 passou em FFmpeg
  e no Chromium do sistema, usado no E2E final de navegador.
- Teste Playwright inicialmente tentou eval bloqueado pela CSP; teste corrigido
  para aguardar elementos, sem afrouxar a CSP da aplicação.
- Cache de modelos no home era somente leitura; download explícito refeito no
  workspace. Nenhuma credencial ou token necessário para esse modelo público.

Reprodução:

```powershell
uv sync --locked
uv run --locked pytest -q
uv run python scripts/studio_e2e.py --output .\studio-data\e2e
```

QC verifica decodificação integral, resolução, duração, codecs, duração de áudio,
nível/pico, intervalos pretos e correspondência SRT/projeto. Não comprova que a
legenda corresponde foneticamente à voz nem que o vídeo é profissional. Revisão
humana permanece explícita. Algumas verificações são conservadoras: silêncio
intencional/tela preta podem exigir revisão, sem exclusão automática de cenas.

## Continuação após o checkpoint

Camadas de texto: dois renders reais comparados por pixels antes/durante/depois
do intervalo. A diferença aparece somente quando a camada deve estar visível.
Prévia de capa e capa final têm SHA256 idênticos com os mesmos parâmetros.
ZIP: oito arquivos permitidos; sem logs/entradas; rejeita hash adulterado e limpa
o temporário após o download. Testes adicionais de concorrência enviam16pedidos
paralelos para a mesma chave e verificam um único job. Recuperação respeita lock
de worker sobrevivente. Caminhos com espaços e acentos testados no render.

Navegador ampliado: camada de texto, prévia de capa e downloadZIP também passaram.
Roteiro executável do teste: `scripts/studio_browser_e2e.py`. Exemplo, com Studio
já iniciado e fixtures produzidas pelo E2E anterior:

```powershell
uv run --with playwright==1.56.0 python scripts/studio_browser_e2e.py --fixtures .\studio-data\e2e --output .\studio-data\browser-test --browser 'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

O Chromium de teste precisa suportar H.264/AAC. Esse script é executado
explicitamente, separado da suíte pytest, e não instala navegador silenciosamente.

A integração real VoiceLabs produziu quatro falas baixadas e um MP4 local20s
com música, quatro cortes, camadas e SRT por frase. QC técnico aprovado; sotaque
e termos comerciais ainda não aprovados. Áudio não enviado ao GitHub.

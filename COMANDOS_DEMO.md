# Demonstração executada

Ambiente: Python 3.12.14, FFmpeg do ambiente, Linux x86-64.
Job: `ddc55657196a4ac782048f0ba838e022`.

```bash
cd /workspace/output/att-dos-games
uv sync --locked
uv run python -m attgames produzir --tema "Rumores e fontes oficiais" --duracao 35
uv run python -m attgames revisar --id ddc55657196a4ac782048f0ba838e022
uv run python -m attgames status --id ddc55657196a4ac782048f0ba838e022
uv run pytest -q
```

Resultado: `review_required`; QC técnico passou; publicação bloqueada.
Vídeo: `data/ddc55657196a4ac782048f0ba838e022/final.mp4`.
Capa, SRT, texto e relatórios estão na mesma pasta.
Sem música, sem gameplay e sem fontes de notícias nesta demonstração.
A narração usa eSpeak NG com seleção explícita `pt-br`; não foi realizada
aprovação humana de sotaque/pronúncia.

Se o cache padrão não for gravável no ambiente gerenciado, use
`UV_CACHE_DIR=/workspace/work/uv` antes dos comandos uv, como nesta execução.

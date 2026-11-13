@echo off
setlocal
cd /d "%~dp0"
set UV_CACHE_DIR=%CD%\.uv-cache
where uv >nul 2>nul || (echo Instale o uv: https://docs.astral.sh/uv/ & pause & exit /b 1)
uv sync --locked || (echo Falha ao instalar dependencias. & pause & exit /b 1)
echo Abrindo ATT DOS GAMES Studio em http://127.0.0.1:8765
uv run --locked python -m attstudio

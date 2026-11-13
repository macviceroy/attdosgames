@echo off
setlocal
cd /d "%~dp0"
set UV_CACHE_DIR=%CD%\.uv-cache
echo Instalando transcricao local faster-whisper (CPU, sem API paga)...
uv sync --locked --extra transcription || goto :error
uv run --locked --extra transcription python scripts\setup_studio_ai.py || goto :error
echo.
echo Concluido. Agora execute iniciar-studio.cmd
pause
exit /b 0
:error
echo Falha na instalacao. Confira internet, Python 3.12 e o log acima.
pause
exit /b 1

@echo off
setlocal
cd /d "%~dp0"
set UV_CACHE_DIR=%CD%\.uv-cache
if exist ".venv\Scripts\python.exe" goto :start
echo Primeira execucao: instalando dependencias uma unica vez...
call scripts\ensure-uv.cmd
if errorlevel 1 (pause & exit /b 1)
call %ATT_UV% sync --locked || (echo Falha ao instalar dependencias. & pause & exit /b 1)
:start
echo Abrindo ATT DOS GAMES Studio em http://127.0.0.1:8765
echo Versao esperada: studio-2026.11.13-r2
".venv\Scripts\python.exe" -m attstudio
if errorlevel 1 (
  echo.
  echo O Studio encerrou com erro. Copie a mensagem acima antes de fechar.
  pause
)

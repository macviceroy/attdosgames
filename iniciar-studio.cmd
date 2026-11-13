@echo off
setlocal
cd /d "%~dp0"
set UV_CACHE_DIR=%CD%\.uv-cache
call scripts\ensure-uv.cmd
if errorlevel 1 (pause & exit /b 1)
call %ATT_UV% sync --locked || (echo Falha ao instalar dependencias. & pause & exit /b 1)
echo Abrindo ATT DOS GAMES Studio em http://127.0.0.1:8765
call %ATT_UV% run --locked python -m attstudio

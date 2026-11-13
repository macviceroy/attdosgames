@echo off
setlocal
cd /d "%~dp0"
set UV_CACHE_DIR=%CD%\.uv-cache
if exist "studio-data\models\faster-whisper-small\config.json" (
  echo A IA local ja esta instalada. Nao sera baixada novamente.
  pause
  exit /b 0
)
call scripts\ensure-uv.cmd
if errorlevel 1 (pause & exit /b 1)
echo Instalando transcricao local faster-whisper (CPU, sem API paga)...
call %ATT_UV% sync --locked --extra transcription || goto :error
call %ATT_UV% run --locked --extra transcription python scripts\setup_studio_ai.py || goto :error
echo.
echo Concluido. Agora execute iniciar-studio.cmd
pause
exit /b 0
:error
echo Falha na instalacao. Confira internet, Python 3.12 e o log acima.
pause
exit /b 1

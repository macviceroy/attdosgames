param([switch]$Transcription)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
foreach ($exe in @('uv','ffmpeg','ffprobe')) {
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
        throw "Falta $exe no PATH. Instale pelos comandos documentados em docs/STUDIO_WINDOWS.md e reabra o terminal."
    }
}
$arguments = @('sync','--locked')
if ($Transcription) { $arguments += @('--extra','transcription') }
& uv @arguments
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias.' }
& uv run --locked python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw 'Testes falharam. Nao ignore a saida.' }
Write-Host 'Instalacao concluida. Execute .\scripts\start-studio.ps1'

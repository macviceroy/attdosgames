param([int]$Port = 8765, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
foreach ($exe in @('uv','ffmpeg','ffprobe')) {
    if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
        throw "Falta $exe no PATH. Consulte docs/STUDIO_WINDOWS.md."
    }
}
$arguments = @('run','--locked','attstudio','--port',"$Port")
if ($NoBrowser) { $arguments += '--no-browser' }
& uv @arguments
if ($LASTEXITCODE -ne 0) { throw "Studio encerrou com codigo $LASTEXITCODE" }

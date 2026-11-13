@echo off
rem Bootstrap compartilhado. Nao use setlocal: ATT_UV precisa voltar ao chamador.
where uv >nul 2>nul
if not errorlevel 1 (
  set "ATT_UV=uv"
  exit /b 0
)

echo O uv nao esta instalado. Preparando automaticamente...
py -3.12 --version >nul 2>nul
if errorlevel 1 goto :install_python

py -3.12 -m pip --version >nul 2>nul
if errorlevel 1 py -3.12 -m ensurepip --upgrade
echo Instalando uv no seu usuario do Windows...
py -3.12 -m pip install --user --upgrade uv
if errorlevel 1 goto :uv_error
py -3.12 -m uv --version >nul 2>nul
if errorlevel 1 goto :uv_error
set "ATT_UV=py -3.12 -m uv"
exit /b 0

:install_python
where winget >nul 2>nul
if errorlevel 1 goto :python_manual
echo Python 3.12 nao encontrado. Instalando com winget no seu usuario...
winget install --id Python.Python.3.12 -e --scope user --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto :python_manual
echo.
echo Python 3.12 foi instalado. Feche esta janela e execute o CMD novamente.
exit /b 2

:python_manual
echo.
echo Python 3.12 nao foi encontrado e o winget nao conseguiu instala-lo.
echo Instale pelo endereco: https://www.python.org/downloads/release/python-31210/
echo Marque a opcao Add Python to PATH e execute este CMD novamente.
exit /b 1

:uv_error
echo.
echo Nao foi possivel instalar o uv pelo Python 3.12.
echo Tente no PowerShell: py -3.12 -m pip install --user uv
exit /b 1

@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  Build local - Enviar Assinaturas D4Sign
echo ============================================

if exist "venv\Scripts\python.exe" (
    set PY=venv\Scripts\python.exe
) else (
    set PY=python
)
set PIP=%PY% -m pip
set PYINST=%PY% -m PyInstaller

for /f "usebackq delims=" %%v in (`%PY% -c "import version; print(version.VERSION)"`) do set VERSION=%%v
echo Versao: %VERSION%
echo.

echo [1/4] Gerando icone...
%PY% create_icon.py

echo [2/4] Instalando dependencias de build...
%PIP% install -r requirements-build.txt -q
if %ERRORLEVEL% neq 0 ( echo ERRO ao instalar dependencias & pause & exit /b 1 )

echo [3/4] Compilando executavel...
if exist dist rmdir /s /q dist
%PYINST% main.spec --noconfirm
if %ERRORLEVEL% neq 0 ( echo ERRO no PyInstaller & pause & exit /b 1 )
if not exist "dist\EnviarAssinaturas.exe" (
    echo ERRO: dist\EnviarAssinaturas.exe nao encontrado
    pause & exit /b 1
)

echo [4/4] Calculando SHA-256...
for /f "usebackq delims=" %%h in (`powershell -NoProfile -Command "(Get-FileHash 'dist\EnviarAssinaturas.exe' -Algorithm SHA256).Hash.ToLower()"`) do set SHA256=%%h
echo %SHA256%  EnviarAssinaturas.exe > dist\EnviarAssinaturas.exe.sha256

echo.
echo ============================================
echo  Build concluido! Versao %VERSION%
echo  Executavel: dist\EnviarAssinaturas.exe
echo ============================================
pause

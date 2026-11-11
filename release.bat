@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  Release - Enviar Assinaturas D4Sign
echo ============================================

:: Detectar Python / venv
if exist "venv\Scripts\python.exe" (
    set PY=venv\Scripts\python.exe
) else (
    set PY=python
)
set PIP=%PY% -m pip
set PYINST=%PY% -m PyInstaller

:: Ler versao do version.py
for /f "usebackq delims=" %%v in (`%PY% -c "import version; print(version.VERSION)"`) do set VERSION=%%v
if "%VERSION%"=="" (
    echo ERRO: nao foi possivel ler VERSION de version.py
    pause & exit /b 1
)
set TAG=v%VERSION%
echo Versao: %TAG%
echo.

:: Verificar se tag ja existe no remoto
git fetch --tags -q 2>nul
git rev-parse "%TAG%" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ERRO: tag %TAG% ja existe.
    echo Incremente VERSION em version.py antes de fazer release.
    pause & exit /b 1
)

:: ===================================================
:: PASSO 1: Enviar repositorio completo para o GitHub
:: ===================================================
echo [1/6] Enviando repositorio para o GitHub...
git add .
git commit -m "chore: release %TAG%" 2>nul
if %ERRORLEVEL% neq 0 echo Sem alteracoes novas para commitar.

git push
if %ERRORLEVEL% neq 0 (
    echo ERRO: falha no git push. Verifique sua conexao e permissoes.
    pause & exit /b 1
)
echo Repositorio enviado.
echo.

:: ===================================================
:: PASSO 2: Verificar icone
:: ===================================================
echo [2/6] Verificando icone...
if not exist "logo_facto.ico" (
    echo ERRO: logo_facto.ico nao encontrado na pasta do projeto.
    pause & exit /b 1
)

:: ===================================================
:: PASSO 3: Instalar dependencias de build
:: ===================================================
echo [3/6] Instalando dependencias de build...
if exist "venv\Lib\site-packages\~ip" rmdir /s /q "venv\Lib\site-packages\~ip" 2>nul
%PIP% install -r requirements-build.txt -q
if %ERRORLEVEL% neq 0 ( echo ERRO ao instalar dependencias & pause & exit /b 1 )

:: ===================================================
:: PASSO 4: Compilar executavel
:: ===================================================
echo [4/6] Compilando executavel...
if exist dist rmdir /s /q dist
%PYINST% main.spec --noconfirm
if %ERRORLEVEL% neq 0 ( echo ERRO no PyInstaller & pause & exit /b 1 )
if not exist "dist\EnviarAssinaturas.exe" (
    echo ERRO: dist\EnviarAssinaturas.exe nao encontrado
    pause & exit /b 1
)

:: ===================================================
:: PASSO 5: Calcular SHA-256
:: ===================================================
echo [5/6] Calculando SHA-256...
for /f "usebackq delims=" %%h in (`powershell -NoProfile -Command "(Get-FileHash 'dist\EnviarAssinaturas.exe' -Algorithm SHA256).Hash.ToLower()"`) do set SHA256=%%h
echo %SHA256%  EnviarAssinaturas.exe > dist\EnviarAssinaturas.exe.sha256
echo SHA-256: %SHA256%
echo.

:: ===================================================
:: PASSO 6: Criar tag e release no GitHub
:: ===================================================
echo [6/6] Criando tag e publicando release %TAG% no GitHub...
git tag %TAG%
git push origin %TAG%
if %ERRORLEVEL% neq 0 (
    git tag -d %TAG% >nul 2>&1
    echo ERRO ao enviar tag para o GitHub
    pause & exit /b 1
)

set NOTES_FILE=%TEMP%\release_notes_%VERSION%.md
(
    echo ## Instalacao
    echo.
    echo 1. Baixe **EnviarAssinaturas.exe**
    echo 2. Baixe **.env.example**, renomeie para **.env** e preencha as credenciais
    echo 3. Baixe **planilha_exemplo.xlsx** como modelo para seus documentos
    echo 4. Coloque os tres arquivos na mesma pasta
    echo 5. Execute EnviarAssinaturas.exe
    echo.
    echo **SHA-256:** `%SHA256%`
) > "%NOTES_FILE%"

gh release create %TAG% ^
    "dist\EnviarAssinaturas.exe" ^
    "dist\EnviarAssinaturas.exe.sha256" ^
    ".env.example" ^
    "planilha_exemplo.xlsx" ^
    --title "Enviar Assinaturas D4Sign %TAG%" ^
    --notes-file "%NOTES_FILE%"

del "%NOTES_FILE%" >nul 2>&1

if %ERRORLEVEL% neq 0 (
    echo ERRO ao criar release no GitHub. Verifique se o gh CLI esta autenticado.
    pause & exit /b 1
)

echo.
echo ============================================
echo  Release %TAG% publicada com sucesso!
echo  https://github.com/DaviTSelect/enviar-assinaturas-d4sign/releases/tag/%TAG%
echo ============================================
pause

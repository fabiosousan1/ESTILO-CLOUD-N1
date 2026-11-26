@echo off
setlocal
set "HYPERFRAMES_NO_TELEMETRY=1"
set "DO_NOT_TRACK=1"
set "ROOT=%USERPROFILE%\Downloads\N1_HYPERFRAMES"
if not exist "%ROOT%" mkdir "%ROOT%"
cd /d "%ROOT%" || exit /b 1
where node >nul 2>&1
if errorlevel 1 goto node_missing
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 22 ? 0 : 1)"
if errorlevel 1 goto node_missing
where ffmpeg >nul 2>&1
if errorlevel 1 goto fail
where ffprobe >nul 2>&1
if errorlevel 1 goto fail
if not exist package.json call npm init -y
if errorlevel 1 goto fail
call npm install --save-exact hyperframes
if errorlevel 1 goto fail
call npx --no-install hyperframes browser ensure
if errorlevel 1 goto fail
call npx --no-install hyperframes doctor
if errorlevel 1 goto fail
echo Instalacao executada. Confira diagnostico acima.
echo Nenhuma API paga foi configurada.
exit /b 0
:node_missing
echo Instale Node.js 22 ou superior em https://nodejs.org/en/download
echo Depois abra novo CMD e execute novamente.
exit /b 2
:fail
echo Falha na instalacao ou dependencia ausente. Confira mensagens acima.
exit /b 1

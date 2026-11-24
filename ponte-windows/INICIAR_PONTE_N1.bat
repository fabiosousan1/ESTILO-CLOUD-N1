@echo off
chcp 65001 >nul
title ESTILO CLOUD N1 - CONEXAO WINDOWS
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
 echo Instale Python 3 e marque Add Python to PATH.
 pause
 exit /b 1
)
py -3.12 -c "import sys" >nul 2>nul
if errorlevel 1 (
 echo Python 3.12 nao encontrado. Instale Python 3.12 antes de continuar.
 pause
 exit /b 1
)
where ffmpeg >nul 2>nul
if errorlevel 1 (
 echo FFmpeg nao encontrado. Instale pelo terminal: winget install Gyan.FFmpeg
 echo Depois feche e abra novamente esta janela.
 pause
 exit /b 1
)
py -3.12 -c "import av; import faster_whisper; assert av.__version__ == '15.1.0'" >nul 2>nul
if errorlevel 1 (
 echo Instalando legendas gratuitas Whisper. Pode levar alguns minutos...
 py -3.12 -m pip install --only-binary=:all: av==15.1.0 faster-whisper==1.2.1
 if errorlevel 1 (
  echo Falha ao instalar Whisper.
  pause
  exit /b 1
 )
)
py -3.12 ponte_n1.py
if errorlevel 1 echo Verifique se Python esta instalado e se a porta 8765 esta livre.
pause

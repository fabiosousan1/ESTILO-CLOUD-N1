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
where ffmpeg >nul 2>nul
if errorlevel 1 (
 echo FFmpeg nao encontrado. Instale pelo terminal: winget install Gyan.FFmpeg
 echo Depois feche e abra novamente esta janela.
 pause
 exit /b 1
)
py -3 -c "import faster_whisper" >nul 2>nul
if errorlevel 1 (
 echo Instalando legendas gratuitas Whisper. Pode levar alguns minutos...
 py -3 -m pip install faster-whisper
 if errorlevel 1 (
  echo Falha ao instalar Whisper.
  pause
  exit /b 1
 )
)
py -3 ponte_n1.py
if errorlevel 1 echo Verifique se Python esta instalado e se a porta 8765 esta livre.
pause

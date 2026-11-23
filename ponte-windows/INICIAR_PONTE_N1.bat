@echo off
title ESTILO CLOUD N1 - CONEXAO WINDOWS
cd /d "%~dp0"
py -3 ponte_n1.py
if errorlevel 1 echo Verifique se Python esta instalado e se a porta 8765 esta livre.
pause

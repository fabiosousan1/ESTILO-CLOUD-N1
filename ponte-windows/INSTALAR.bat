@echo off
title INSTALAR PONTE ESTILO N1
echo Instalando dependencias do baixador...
py -3 -m pip install --upgrade gallery-dl yt-dlp
if errorlevel 1 (
 echo Falha na instalacao. Verifique Python e internet.
 pause
 exit /b 1
)
echo.
echo Instalacao concluida. Execute INICIAR_PONTE_N1.bat
pause

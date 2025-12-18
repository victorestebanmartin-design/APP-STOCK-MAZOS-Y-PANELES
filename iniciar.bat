@echo off
echo ============================================
echo Iniciando Stock Mazos y Paneles
echo ============================================
echo.

REM Activar entorno virtual si existe
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Iniciar aplicacion
echo Iniciando servidor Flask...
echo.
echo La aplicacion estara disponible en:
echo.
echo     http://localhost:5000
echo.
echo Presione Ctrl+C para detener el servidor
echo.
python app.py

pause

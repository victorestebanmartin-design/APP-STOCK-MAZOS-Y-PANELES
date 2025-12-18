@echo off
echo ============================================
echo Instalacion - Stock Mazos y Paneles
echo ============================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado
    echo Por favor, instale Python 3.8 o superior
    pause
    exit /b 1
)

echo [1/4] Python detectado
echo.

REM Crear entorno virtual (opcional)
echo [2/4] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ADVERTENCIA: No se pudo crear entorno virtual
    echo Continuando con Python global...
) else (
    echo Entorno virtual creado
    call venv\Scripts\activate.bat
)
echo.

REM Instalar dependencias
echo [3/4] Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install Flask==3.0.0
python -m pip install Flask-SQLAlchemy==3.1.1
python -m pip install pandas==2.1.4
python -m pip install openpyxl==3.1.2
python -m pip install python-dateutil==2.8.2
echo.

REM Inicializar base de datos
echo [4/4] Inicializando base de datos...
python app.py --init-only
echo.

echo ============================================
echo INSTALACION COMPLETADA
echo ============================================
echo.
echo Para iniciar la aplicacion:
echo   1. Ejecute: iniciar.bat
echo   2. Abra su navegador en: http://localhost:5000
echo.
pause

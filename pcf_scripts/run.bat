@echo off
echo ========================================
echo   CEAPSI - Sistema PCF
echo   Precision Call Forecast
echo ========================================
echo.

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en el PATH
    echo Por favor instala Python 3.8 o superior desde https://python.org
    pause
    exit /b 1
)

echo ✅ Python detectado
echo.

REM Verificar si pip está disponible
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip no está disponible
    pause
    exit /b 1
)

echo ✅ pip detectado
echo.

REM Instalar dependencias si es necesario
echo 📦 Verificando dependencias...
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo ❌ Error instalando dependencias
    echo Intentando instalación manual...
    pip install streamlit pandas numpy plotly scikit-learn prophet statsmodels openpyxl schedule
)

echo ✅ Dependencias verificadas
echo.

REM Verificar datos
echo 🔍 Verificando datos...
if exist "..\backups\alodesk_reporte_llamadas_jan2023_to_jul2025.csv" (
    echo ✅ Archivo de datos encontrado
) else (
    echo ⚠️  Archivo de datos no encontrado en la ruta esperada
    echo    Asegúrate de tener: ..\backups\alodesk_reporte_llamadas_jan2023_to_jul2025.csv
)

echo.
echo 🚀 Iniciando CEAPSI Sistema PCF...
echo.
echo 📋 Instrucciones:
echo    1. Se abrirá automáticamente en tu navegador
echo    2. Si no se abre, ve a: http://localhost:8501
echo    3. Para detener el servidor, presiona Ctrl+C
echo.
echo ⏳ Iniciando servidor Streamlit...

REM Iniciar Streamlit
streamlit run app.py

pause

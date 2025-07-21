#!/bin/bash

echo "========================================"
echo "  CEAPSI - Sistema PCF"
echo "  Precision Call Forecast"
echo "========================================"
echo

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 no está instalado"
    echo "Por favor instala Python 3.8 o superior"
    exit 1
fi

echo "✅ Python detectado"

# Verificar si pip está disponible
if ! command -v pip3 &> /dev/null; then
    echo "❌ ERROR: pip3 no está disponible"
    exit 1
fi

echo "✅ pip detectado"

# Instalar dependencias si es necesario
echo "📦 Verificando dependencias..."
pip3 install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    echo "❌ Error instalando dependencias"
    echo "Intentando instalación manual..."
    pip3 install streamlit pandas numpy plotly scikit-learn prophet statsmodels openpyxl schedule
fi

echo "✅ Dependencias verificadas"

# Verificar datos
echo "🔍 Verificando datos..."
if [ -f "../backups/alodesk_reporte_llamadas_jan2023_to_jul2025.csv" ]; then
    echo "✅ Archivo de datos encontrado"
else
    echo "⚠️  Archivo de datos no encontrado en la ruta esperada"
    echo "   Asegúrate de tener: ../backups/alodesk_reporte_llamadas_jan2023_to_jul2025.csv"
fi

echo
echo "🚀 Iniciando CEAPSI Sistema PCF..."
echo
echo "📋 Instrucciones:"
echo "   1. Se abrirá automáticamente en tu navegador"
echo "   2. Si no se abre, ve a: http://localhost:8501"
echo "   3. Para detener el servidor, presiona Ctrl+C"
echo
echo "⏳ Iniciando servidor Streamlit..."

# Iniciar Streamlit
streamlit run app.py

#!/usr/bin/env python3
"""
Script de prueba para verificar si data_preparation.py funciona correctamente
"""

import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Importar las clases necesarias
    from data_preparation import DataPreparationProphet
    import pandas as pd
    import json
    
    print("🧪 INICIANDO PRUEBA DE PREPARACIÓN DE DATOS")
    print("=" * 50)
    
    # Verificar que existe el archivo de datos
    base_path = r"C:\Users\edgar\OneDrive\Documentos\BBDD CEAPSI\claude\analisis_resultados"
    datos_input = os.path.join(base_path, "datos_normalizados.json")
    
    if not os.path.exists(datos_input):
        print(f"❌ No se encontró el archivo: {datos_input}")
        sys.exit(1)
    
    print(f"✅ Archivo de datos encontrado: {datos_input}")
    
    # Probar la carga de datos
    preparador = DataPreparationProphet(datos_input)
    datos_normalizados = preparador.cargar_datos_normalizados()
    
    if datos_normalizados is None:
        print("❌ Error cargando datos normalizados")
        sys.exit(1)
    
    print("✅ Datos normalizados cargados exitosamente")
    
    # Probar consolidación de datos
    df_transacciones = preparador.consolidar_datos_diarios(datos_normalizados)
    print(f"✅ Datos consolidados: {len(df_transacciones)} transacciones")
    
    # Verificar columnas
    print(f"📋 Columnas disponibles: {list(df_transacciones.columns)}")
    
    # Verificar tipos de transacciones
    tipos = df_transacciones['tipo'].value_counts()
    print(f"📊 Tipos de transacciones:")
    for tipo, count in tipos.items():
        print(f"   {tipo}: {count}")
    
    # Verificar si hay reservas
    reservas = df_transacciones[df_transacciones['tipo'] == 'reserva']
    print(f"📋 Reservas encontradas: {len(reservas)}")
    
    if len(reservas) > 0:
        print(f"📋 Especialidades en reservas: {reservas['especialidad'].value_counts()}")
    
    # Probar cálculo de variable objetivo
    df_objetivo = preparador.calcular_variable_objetivo(df_transacciones)
    print(f"✅ Variable objetivo calculada: {len(df_objetivo)} días")
    print(f"📈 Promedio horas/día: {df_objetivo['y'].mean():.1f}")
    
    # Probar cálculo de regresores
    df_regresores = preparador.calcular_regresores(df_transacciones)
    print(f"✅ Regresores calculados: {len(df_regresores)} días")
    print(f"🔧 Columnas de regresores: {[col for col in df_regresores.columns if col != 'ds']}")
    
    print("\n🎉 PRUEBA COMPLETADA EXITOSAMENTE")
    print("El script data_preparation.py debería funcionar correctamente ahora.")
    
except Exception as e:
    print(f"❌ Error en la prueba: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

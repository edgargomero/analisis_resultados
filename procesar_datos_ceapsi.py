#!/usr/bin/env python3
"""
Script de procesamiento de datos CEAPSI
Normalización y análisis de carga laboral enero-junio 2025
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import numpy as np
import os

def normalizar_cargo(cargo):
    if not cargo or not isinstance(cargo, str):
        return 'NO_ESPECIFICADO'
    cargo = cargo.strip().upper()
    if 'CALL' in cargo:
        return 'CALL CENTER'
    if 'SECRETARIA' in cargo:
        return 'SECRETARIA'
    if 'PROFESIONAL' in cargo:
        return 'PROFESIONAL'
    if 'JEFA' in cargo:
        return 'JEFA DE SUCURSAL'
    if 'ADMIN' in cargo:
        return 'ADMINISTRACION'
    return cargo

def main():
    print("=== PROCESAMIENTO DE DATOS CEAPSI ===\n")
    
    # Rutas de archivos
    base_path = r"C:\Users\edgar\OneDrive\Documentos\BBDD CEAPSI\claude"
    output_path = r"C:\Users\edgar\OneDrive\Documentos\BBDD CEAPSI\claude\analisis_resultados"
    
    # NUEVO: Crear subcarpeta con timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_subfolder = os.path.join(output_path, f"resultados_{timestamp}")
    os.makedirs(output_subfolder, exist_ok=True)
    print(f"📁 Carpeta de resultados creada: {output_subfolder}")
    
    # Procesar cada fuente de datos
    datos_normalizados = {
        'reservas': procesar_reservas(base_path),
        'conversaciones': procesar_conversaciones(base_path),
        'llamadas': procesar_llamadas(base_path),
        'metadatos': {
            'fecha_procesamiento': datetime.now().isoformat(),
            'periodo': 'enero-junio 2025',
            'dias_incluidos': 'lunes a sábado',
            'fuentes': ['historiales2025.csv', 'conversaciones.csv', 'llamadas.csv']
        }
    }
    
    # Generar análisis
    metricas_carga = analizar_carga_laboral(datos_normalizados)
    mapa_calor_datos = generar_mapa_calor(datos_normalizados)
    
    # Guardar resultados en la subcarpeta
    guardar_resultados(output_subfolder, datos_normalizados, metricas_carga, mapa_calor_datos)
    calcular_personal_necesario_por_hora(datos_normalizados, output_subfolder)
    
    print("\n=== PROCESAMIENTO COMPLETADO ===")
    return datos_normalizados, metricas_carga, mapa_calor_datos


def procesar_reservas(base_path):
    """Procesa el archivo de reservas leyendo el formato de fecha Zulu/ISO 8601."""
    try:
        print("📋 Procesando reservas...")
        archivo = f"{base_path}\\datos de sistema de reservas - reservo\\historiales2025.csv"

        # 1. Leer el archivo forzando la separación de columnas (método robusto).
        df_raw = pd.read_csv(archivo, sep='|', header=None, encoding='utf-8-sig')
        df = df_raw[0].str.split(';', expand=True)
        df.columns = df.iloc[0]
        df = df.drop(0).reset_index(drop=True)

        print(f"Total registros reservas: {len(df)}")

        # --- INICIO DE LA CORRECCIÓN DE FECHA ---
        # 2. Convertir la columna 'inicio' a datetime SIN especificar un formato.
        # pandas detectará automáticamente el formato Zulu/ISO 8601 (AAAA-MM-DDTHH:MM:SSZ).
        df['inicio_dt'] = pd.to_datetime(df['inicio'], errors='coerce')
        df['fin_dt'] = pd.to_datetime(df['fin'], errors='coerce')
        # --- FIN DE LA CORRECCIÓN DE FECHA ---

        # 3. Eliminar filas donde la fecha de inicio no se pudo convertir.
        df.dropna(subset=['inicio_dt'], inplace=True)
        
        # Si no quedan datos después de la limpieza, el problema persiste en los datos.
        if df.empty:
            print("❌ No quedaron datos después de limpiar fechas. Revisa el contenido del CSV.")
            print("✅ Reservas normalizadas: 0")
            return []

        reservas_normalizadas = []
        for index, row in df.iterrows():
            fecha = row['inicio_dt']
            
            # El resto del código de filtrado y procesamiento funciona como antes.
            if (fecha.year == 2025 and 1 <= fecha.month <= 6 and 1 <= fecha.dayofweek + 1 <= 6):
                
                duracion = 45 # default
                if pd.notna(row['fin_dt']):
                    diff_seconds = (row['fin_dt'] - fecha).total_seconds()
                    if diff_seconds > 0:
                        duracion = diff_seconds / 60
                        duracion = max(15, min(120, duracion))

                registro = {
                    'id': row.get('uuid_cita', f'res_{index}'),
                    'fecha': fecha.isoformat(),
                    'fecha_str': fecha.strftime('%Y-%m-%d'),
                    'dia_semana': fecha.dayofweek + 1,
                    'hora': fecha.hour,
                    'mes': fecha.month,
                    'profesional': row.get('profesional_nombre', 'No especificado'),
                    'especialidad': row.get('profesional_normalizado', 'General'),
                    'estado': row.get('estado_descripcion', 'No confirmado'),
                    'motivo': row.get('motivo', 'Consulta médica'),
                    'cargo': normalizar_cargo(row.get('usuario_cargo', 'PROFESIONAL')),
                    'usuario': row.get('profesional_nombre', 'NO_ESPECIFICADO'),
                    'duracion': int(duracion),
                    'tipo': 'reserva'
                }
                reservas_normalizadas.append(registro)
        
        print(f"✅ Reservas normalizadas: {len(reservas_normalizadas)}")
        return reservas_normalizadas
        
    except Exception as e:
        print(f"❌ Error fatal procesando reservas: {e}")
        import traceback
        traceback.print_exc()
        return []


def procesar_conversaciones(base_path):
    """Procesa el archivo de conversaciones de Alodesk"""
    try:
        print("💬 Procesando conversaciones...")
        archivo = f"{base_path}\\datos de sistema de comunicacion cliente alodesk\\csv\\conversaciones.csv"
        
        # Corrección para DtypeWarning
        df = pd.read_csv(archivo, sep=';', encoding='utf-8', dtype={16: str, 17: str, 18: str, 19: str})
        print(f"Total registros conversaciones: {len(df)}")
        
        conversaciones_normalizadas = []
        
        for index, row in df.iterrows():
            try:
                fecha_str = row.get('FECHA_INICIO')
                if pd.isna(fecha_str):
                    continue
                
                fecha_inicio = pd.to_datetime(fecha_str, format='%d-%m-%Y %H:%M')
                
                # --- INICIO DE CORRECCIÓN DE DURACIÓN ---
                duracion = 10  # default 10 minutos
                fecha_fin_str = row.get('fecha final - fini')
                
                if pd.notna(fecha_fin_str):
                    try:
                        # Asume que la fecha final tiene el mismo formato
                        fecha_fin = pd.to_datetime(fecha_fin_str, format='%d-%m-%Y %H:%M')
                        # Calcula la diferencia en minutos
                        diff_min = (fecha_fin - fecha_inicio).total_seconds() / 60
                        if diff_min > 0:
                            duracion = diff_min
                    except ValueError:
                        # Si el formato falla, intenta interpretar solo la hora como en el original
                        if isinstance(fecha_fin_str, str) and ':' in fecha_fin_str:
                             parts = fecha_fin_str.split(':')
                             if len(parts) >= 2:
                                duracion = int(parts[0]) * 60 + int(parts[1]) # Mantener como fallback
                # --- FIN DE CORRECCIÓN DE DURACIÓN ---

                # (El resto de la función permanece igual)
                cargo = row.get('CARGOO') or row.get('cargo2222') or 'CALL CENTER'
                if 1 <= fecha_inicio.dayofweek + 1 <= 6:
                    registro = {
                        'id': row.get('ID', f'conv_{index}'),
                        'fecha': fecha_inicio.isoformat(),
                        'fecha_str': fecha_inicio.strftime('%Y-%m-%d'),
                        'dia_semana': fecha_inicio.dayofweek + 1,
                        'hora': fecha_inicio.hour,
                        'mes': fecha_inicio.month,
                        'agente': row.get('AGENTES', 'No especificado'),
                        'cargo': normalizar_cargo(cargo),
                        'usuario': row.get('AGENTES', 'NO_ESPECIFICADO'),
                        'atendida': row.get('ATENDIDA', '').lower() == 'si',
                        'num_mensajes': int(row.get('NUMERO_MENSAJES', 0)),
                        'duracion': int(duracion),
                        'tipo': 'conversacion'
                    }
                    conversaciones_normalizadas.append(registro)
            except Exception as e:
                continue
        
        print(f"✅ Conversaciones normalizadas: {len(conversaciones_normalizadas)}")
        return conversaciones_normalizadas
    except Exception as e:
        print(f"❌ Error procesando conversaciones: {e}")
        return []
    
# En procesar_datos_ceapsi.py

def procesar_llamadas(base_path):
    """Procesa el archivo de llamadas de Alodesk"""
    try:
        print("📞 Procesando llamadas...")
        archivo = f"{base_path}\\datos de sistema de comunicacion cliente alodesk\\csv\\llamadas.csv"
        
        df = pd.read_csv(archivo, sep=';', encoding='utf-8')
        print(f"Total registros llamadas: {len(df)}")
        
        llamadas_normalizadas = []
        
        for index, row in df.iterrows():
            try:
                fecha_str = row.get('FECHA2')
                if pd.isna(fecha_str):
                    continue
                
                fecha = pd.to_datetime(fecha_str, format='%d-%m-%Y')
                
                # --- INICIO DE CORRECCIÓN DE DURACIÓN ---
                # La duración en este archivo parece ser un string 'H:MM:SS'
                duracion = 5 # default 5 minutos
                duracion_str = row.get('duracion 2', '0:05:00')
                if pd.notna(duracion_str) and isinstance(duracion_str, str) and ':' in duracion_str:
                    parts = duracion_str.split(':')
                    if len(parts) == 3: # Formato HH:MM:SS
                        duracion = int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
                    elif len(parts) == 2: # Formato MM:SS
                        duracion = int(parts[0]) + int(parts[1]) / 60
                # --- FIN DE CORRECCIÓN DE DURACIÓN ---

                # (El resto de la función permanece igual)
                if 1 <= fecha.dayofweek + 1 <= 6:
                    registro = {
                        'id': row.get('UNIQUEID', f'call_{index}'),
                        'fecha': fecha.isoformat(),
                        'fecha_str': fecha.strftime('%Y-%m-%d'),
                        'dia_semana': fecha.dayofweek + 1,
                        'hora': 12,
                        'mes': fecha.month,
                        'agente': row.get('AGENTE', 'No especificado'),
                        'cargo': normalizar_cargo(row.get('CARGO', 'CALL CENTER')),
                        'usuario': row.get('AGENTE', 'NO_ESPECIFICADO'),
                        'atendida': row.get('ATENDIDA', '').lower() == 'si',
                        'duracion': int(duracion),
                        'tiempo_espera': 0,
                        'tipo': 'llamada'
                    }
                    llamadas_normalizadas.append(registro)
            except Exception as e:
                continue
        
        print(f"✅ Llamadas normalizadas: {len(llamadas_normalizadas)}")
        return llamadas_normalizadas
    except Exception as e:
        print(f"❌ Error procesando llamadas: {e}")
        return []
    
def analizar_carga_laboral(datos_normalizados):
    """Genera análisis 360° de carga laboral por cargo"""
    print("📊 Analizando carga laboral...")
    
    # Combinar todos los datos
    todos_datos = (datos_normalizados['reservas'] + 
                   datos_normalizados['conversaciones'] + 
                   datos_normalizados['llamadas'])
    
    carga_por_cargo = {}
    
    for registro in todos_datos:
        cargo = registro.get('cargo', 'NO_ESPECIFICADO')
        
        if cargo not in carga_por_cargo:
            carga_por_cargo[cargo] = {
                'total_transacciones': 0,
                'duracion_total_minutos': 0,
                'por_mes': [0] * 6,
                'por_dia_semana': [0] * 7,
                'por_tipo': {'reserva': 0, 'conversacion': 0, 'llamada': 0},
                'carga_total_horas': 0,
                'promedio_diario': 0
            }
        
        carga_por_cargo[cargo]['total_transacciones'] += 1
        carga_por_cargo[cargo]['duracion_total_minutos'] += registro.get('duracion', 0)
        
        mes = registro.get('mes', 1) - 1  # 0-indexed
        if 0 <= mes < 6:
            carga_por_cargo[cargo]['por_mes'][mes] += 1
        
        dia = registro.get('dia_semana', 1) - 1  # 0-indexed
        if 0 <= dia < 7:
            carga_por_cargo[cargo]['por_dia_semana'][dia] += 1
        
        tipo = registro.get('tipo', 'otro')
        if tipo in carga_por_cargo[cargo]['por_tipo']:
            carga_por_cargo[cargo]['por_tipo'][tipo] += 1
    
    # Calcular métricas derivadas
    for cargo, datos in carga_por_cargo.items():
        datos['carga_total_horas'] = round(datos['duracion_total_minutos'] / 60, 1)
        datos['promedio_diario'] = round(datos['total_transacciones'] / 180, 1)  # 6 meses * 30 días
        datos['duracion_promedio'] = round(
            datos['duracion_total_minutos'] / max(1, datos['total_transacciones']), 1
        )
    
    # Ordenar por carga total
    carga_ordenada = dict(sorted(carga_por_cargo.items(), 
                                key=lambda x: x[1]['total_transacciones'], 
                                reverse=True))
    
    print(f"✅ Análisis de carga completado para {len(carga_ordenada)} cargos")
    return carga_ordenada

def generar_mapa_calor(datos_normalizados):
    """Genera datos para mapa de calor (enero-junio, lunes-sábado)"""
    print("🗺️ Generando datos para mapa de calor...")
    
    # Combinar todos los datos
    todos_datos = (datos_normalizados['reservas'] + 
                   datos_normalizados['conversaciones'] + 
                   datos_normalizados['llamadas'])
    
    # Inicializar matriz 6 meses x 6 días
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio']
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
    
    mapa_datos = []
    
    for mes_idx, mes_nombre in enumerate(meses):
        for dia_idx, dia_nombre in enumerate(dias):
            # Filtrar transacciones para este mes y día
            transacciones = [
                t for t in todos_datos 
                if t.get('mes') == mes_idx + 1 and t.get('dia_semana') == dia_idx + 1
            ]
            
            # Calcular métricas
            num_transacciones = len(transacciones)
            duracion_total = sum(t.get('duracion', 0) for t in transacciones)
            duracion_promedio = duracion_total / max(1, num_transacciones)
            
            # Desglose por tipo
            por_tipo = {'reserva': 0, 'conversacion': 0, 'llamada': 0}
            for t in transacciones:
                tipo = t.get('tipo', 'otro')
                if tipo in por_tipo:
                    por_tipo[tipo] += 1
            
            celda = {
                'mes': mes_nombre,
                'dia': dia_nombre,
                'mes_index': mes_idx,
                'dia_index': dia_idx,
                'transacciones': num_transacciones,
                'duracion_total_minutos': duracion_total,
                'duracion_promedio': round(duracion_promedio, 1),
                'desglose_tipo': por_tipo,
                'intensidad': min(1.0, num_transacciones / 100)  # Normalizado 0-1
            }
            
            mapa_datos.append(celda)
    
    print(f"✅ Mapa de calor generado: {len(mapa_datos)} celdas")
    return mapa_datos

def guardar_resultados(output_path, datos_normalizados, metricas_carga, mapa_calor_datos):
    """Guarda todos los resultados en archivos JSON"""
    print("💾 Guardando resultados...")
    
    try:
        # Datos normalizados
        with open(f"{output_path}\\datos_normalizados.json", 'w', encoding='utf-8') as f:
            json.dump(datos_normalizados, f, indent=2, ensure_ascii=False)
        
        # Métricas de carga laboral
        with open(f"{output_path}\\metricas_carga_laboral.json", 'w', encoding='utf-8') as f:
            json.dump(metricas_carga, f, indent=2, ensure_ascii=False)
        
        # Datos de mapa de calor
        with open(f"{output_path}\\mapa_calor_datos.json", 'w', encoding='utf-8') as f:
            json.dump(mapa_calor_datos, f, indent=2, ensure_ascii=False)
        
        # Resumen ejecutivo
        resumen = generar_resumen_ejecutivo(datos_normalizados, metricas_carga, mapa_calor_datos)
        with open(f"{output_path}\\resumen_ejecutivo.json", 'w', encoding='utf-8') as f:
            json.dump(resumen, f, indent=2, ensure_ascii=False)
        
        print("✅ Todos los resultados guardados exitosamente")
        
    except Exception as e:
        print(f"❌ Error guardando resultados: {e}")

def generar_resumen_ejecutivo(datos_normalizados, metricas_carga, mapa_calor_datos):
    """Genera un resumen ejecutivo con KPIs principales"""
    
    total_reservas = len(datos_normalizados['reservas'])
    total_conversaciones = len(datos_normalizados['conversaciones'])
    total_llamadas = len(datos_normalizados['llamadas'])
    total_transacciones = total_reservas + total_conversaciones + total_llamadas
    
    # Profesionales únicos
    profesionales_unicos = set()
    for reserva in datos_normalizados['reservas']:
        profesionales_unicos.add(reserva.get('profesional', ''))
    
    # Cargo con mayor carga
    cargo_mayor_carga = max(metricas_carga.items(), key=lambda x: x[1]['total_transacciones'])
    
    # Día más ocupado
    transacciones_por_dia = {}
    for celda in mapa_calor_datos:
        dia = celda['dia']
        if dia not in transacciones_por_dia:
            transacciones_por_dia[dia] = 0
        transacciones_por_dia[dia] += celda['transacciones']
    
    dia_mas_ocupado = max(transacciones_por_dia.items(), key=lambda x: x[1])
    
    # Mes más ocupado
    transacciones_por_mes = {}
    for celda in mapa_calor_datos:
        mes = celda['mes']
        if mes not in transacciones_por_mes:
            transacciones_por_mes[mes] = 0
        transacciones_por_mes[mes] += celda['transacciones']
    
    mes_mas_ocupado = max(transacciones_por_mes.items(), key=lambda x: x[1])
    
    resumen = {
        'fecha_generacion': datetime.now().isoformat(),
        'periodo_analisis': 'Enero - Junio 2025',
        'kpis_principales': {
            'total_transacciones': total_transacciones,
            'reservas_medicas': total_reservas,
            'conversaciones_chat': total_conversaciones,
            'llamadas_telefonicas': total_llamadas,
            'profesionales_activos': len(profesionales_unicos),
            'promedio_transacciones_diarias': round(total_transacciones / 180, 1)
        },
        'carga_laboral': {
            'cargo_mayor_carga': cargo_mayor_carga[0],
            'transacciones_cargo_mayor': cargo_mayor_carga[1]['total_transacciones'],
            'total_cargos_analizados': len(metricas_carga)
        },
        'patrones_temporales': {
            'dia_mas_ocupado': dia_mas_ocupado[0],
            'transacciones_dia_pico': dia_mas_ocupado[1],
            'mes_mas_ocupado': mes_mas_ocupado[0],
            'transacciones_mes_pico': mes_mas_ocupado[1]
        },
        'distribucion_por_canal': {
            'reservas_porcentaje': round((total_reservas / total_transacciones) * 100, 1),
            'conversaciones_porcentaje': round((total_conversaciones / total_transacciones) * 100, 1),
            'llamadas_porcentaje': round((total_llamadas / total_transacciones) * 100, 1)
        }
    }
    
    return resumen

def calcular_personal_necesario_por_hora(datos_normalizados, output_path):
    """Calcula la necesidad de personal por hora, semana y cargo"""
    import pandas as pd
    import numpy as np

    # Unificar todas las transacciones
    transacciones = []
    for tipo in ['reservas', 'conversaciones', 'llamadas']:
        for t in datos_normalizados.get(tipo, []):
            transacciones.append({
                'fecha': t['fecha'],
                'hora': int(t['hora']),
                'cargo': t.get('cargo', 'NO_ESPECIFICADO'),
                'duracion': int(t.get('duracion', 0))
            })
    df = pd.DataFrame(transacciones)
    if df.empty:
        print("❌ No hay transacciones para calcular personal necesario.")
        return

    # Convertir todas las fechas a datetime (robusto)
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', utc=True)
    # Elimina filas donde la fecha no se pudo convertir
    df = df.dropna(subset=['fecha'])

    # Ahora sí puedes usar .dt
    df['semana'] = df['fecha'].dt.isocalendar().week
    df['dia_semana'] = df['fecha'].dt.day_name()

    # Agrupar por semana, día, hora, cargo
    agrupado = df.groupby(['semana', 'dia_semana', 'hora', 'cargo']).agg(
        duracion_total_min=('duracion', 'sum')
    ).reset_index()

    # Calcular personal necesario (1 persona = 60 min/hora)
    agrupado['personal_necesario'] = np.ceil(agrupado['duracion_total_min'] / 60).astype(int)

    # Exportar a CSV
    csv_path = f"{output_path}/personal_necesario_por_hora.csv"
    agrupado.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"✅ Personal necesario por hora exportado a: {csv_path}")

    # Exportar a JSON
    json_path = f"{output_path}/personal_necesario_por_hora.json"
    agrupado.to_json(json_path, orient='records', force_ascii=False)
    print(f"✅ Personal necesario por hora exportado a: {json_path}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
CEAPSI - Auditoría Profunda de Datos de Llamadas Alodesk
Diagnóstico completo para mejorar predicciones
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import warnings
warnings.filterwarnings('ignore')

class AuditoriaLlamadasAlodesk:
    """Auditor especializado para datos de llamadas de call center"""
    
    def __init__(self, ruta_datos_llamadas):
        self.ruta_datos = ruta_datos_llamadas
        self.df = None
        self.reporte_calidad = {}
        
    def cargar_y_limpiar_datos(self):
        """Carga datos con validación exhaustiva"""
        try:
            # Cargar con múltiples encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    self.df = pd.read_csv(self.ruta_datos, sep=';', encoding=encoding)
                    print(f"✅ Datos cargados con encoding {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if self.df is None:
                raise ValueError("No se pudo cargar el archivo con ningún encoding")
            
            print(f"📊 Dataset cargado: {len(self.df)} registros, {len(self.df.columns)} columnas")
            print(f"📋 Columnas: {list(self.df.columns)}")
            
            # Limpieza inicial
            self.df.columns = self.df.columns.str.strip()
            
            return True
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def analizar_estructura_temporal(self):
        """Análisis detallado de patrones temporales"""
        
        # Columnas de fecha específicas de tu archivo Alodesk
        columnas_fecha = ['FECHA']  # Tu archivo tiene la columna FECHA
        
        print(f"🕐 Columnas temporales detectadas: {columnas_fecha}")
        print(f"📋 Columnas disponibles en archivo: {list(self.df.columns)}")
        
        # Análisis por cada columna de fecha
        patrones_temporales = {}
        
        for col_fecha in columnas_fecha:
            try:
                # Intentar múltiples formatos de fecha
                formatos = ['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', 
                           '%d-%m-%Y %H:%M', '%Y-%m-%d %H:%M:%S']
                
                fechas_convertidas = None
                formato_exitoso = None
                
                # Para tu formato específico: '02-01-2023 08:08:07'
                try:
                    fechas_convertidas = pd.to_datetime(self.df[col_fecha], format='%d-%m-%Y %H:%M:%S')
                    formato_exitoso = '%d-%m-%Y %H:%M:%S'
                except:
                    try:
                        fechas_convertidas = pd.to_datetime(self.df[col_fecha], infer_datetime_format=True)
                        formato_exitoso = 'auto-detectado'
                    except:
                        continue
                
                if fechas_convertidas is not None:
                    # Análisis temporal detallado
                    patron = {
                        'formato_exitoso': formato_exitoso,
                        'rango_fechas': f"{fechas_convertidas.min()} a {fechas_convertidas.max()}",
                        'total_dias': (fechas_convertidas.max() - fechas_convertidas.min()).days,
                        'dias_unicos': fechas_convertidas.dt.date.nunique(),
                        'valores_nulos': fechas_convertidas.isnull().sum(),
                        'distribucion_dias_semana': fechas_convertidas.dt.day_name().value_counts().to_dict(),
                        'distribucion_meses': fechas_convertidas.dt.month_name().value_counts().to_dict()
                    }
                    
                    patrones_temporales[col_fecha] = patron
                    print(f"✅ {col_fecha}: {patron['rango_fechas']}")
                
            except Exception as e:
                print(f"⚠️ Error procesando {col_fecha}: {e}")
        
        return patrones_temporales
    
    def detectar_llamadas_entrantes_salientes(self):
        """Detecta y separa llamadas entrantes vs salientes"""
        
        # Tu archivo tiene la columna SENTIDO que indica 'in' o 'out'
        columnas_direccion = ['SENTIDO']
        
        print(f"📞 Columnas de dirección detectadas: {columnas_direccion}")
        print(f"🔍 Valores únicos en SENTIDO: {self.df['SENTIDO'].value_counts().to_dict()}")
        
        # Análisis específico para tu archivo
        if 'SENTIDO' in self.df.columns:
            valores_unicos = self.df['SENTIDO'].value_counts()
            print(f"🔍 SENTIDO: {valores_unicos.to_dict()}")
            
            # También analizar ATENDIDA y STATUS
            if 'ATENDIDA' in self.df.columns:
                print(f"🔍 ATENDIDA: {self.df['ATENDIDA'].value_counts().to_dict()}")
            if 'STATUS' in self.df.columns:
                print(f"🔍 STATUS: {self.df['STATUS'].value_counts().to_dict()}")
        
        # Analizar teléfonos en tu archivo
        columnas_telefono = ['TELEFONO']
        
        for col in columnas_telefono:
            if col in self.df.columns and self.df[col].dtype == 'object':
                # Analizar patrones de números
                muestra = self.df[col].dropna().head(100).astype(str)
                longitudes = muestra.str.len()
                print(f"📱 {col}: Longitudes {longitudes.describe()}")
                
                # Detectar patrones de prefijos
                prefijos = muestra.str[:3].value_counts().head(10)
                print(f"📱 Prefijos más comunes: {prefijos.to_dict()}")
        
        return columnas_direccion, columnas_telefono
    
    def analizar_volumenes_diarios(self):
        """Análisis detallado de volúmenes por día"""
        
        # Usar la columna FECHA de tu archivo
        col_fecha = 'FECHA'
        
        if col_fecha not in self.df.columns:
            print("❌ No se encontró la columna FECHA")
            return None
        
        # Convertir fechas usando el formato específico de tu archivo
        try:
            fechas = pd.to_datetime(self.df[col_fecha], format='%d-%m-%Y %H:%M:%S')
            self.df['fecha_procesada'] = fechas
            self.df['fecha_str'] = fechas.dt.date
            
        except Exception as e:
            print(f"❌ Error convirtiendo fechas: {e}")
            try:
                # Fallback con auto-detección
                fechas = pd.to_datetime(self.df[col_fecha], infer_datetime_format=True)
                self.df['fecha_procesada'] = fechas
                self.df['fecha_str'] = fechas.dt.date
            except Exception as e2:
                print(f"❌ Error en fallback: {e2}")
                return None
        
        # Filtrar solo días laborales (lunes-viernes)
        dias_laborales = self.df[fechas.dt.dayofweek < 5].copy()
        
        # Análisis de volúmenes
        volumenes_diarios = dias_laborales.groupby('fecha_str').size()
        
        estadisticas_volumen = {
            'promedio_diario': volumenes_diarios.mean(),
            'mediana_diaria': volumenes_diarios.median(),
            'desviacion_std': volumenes_diarios.std(),
            'coeficiente_variacion': volumenes_diarios.std() / volumenes_diarios.mean(),
            'dia_maximo': volumenes_diarios.idxmax(),
            'volumen_maximo': volumenes_diarios.max(),
            'dia_minimo': volumenes_diarios.idxmin(),
            'volumen_minimo': volumenes_diarios.min(),
            'total_dias': len(volumenes_diarios),
            'dias_cero': (volumenes_diarios == 0).sum()
        }
        
        # Detectar outliers
        Q1 = volumenes_diarios.quantile(0.25)
        Q3 = volumenes_diarios.quantile(0.75)
        IQR = Q3 - Q1
        outliers_superiores = volumenes_diarios[volumenes_diarios > Q3 + 1.5 * IQR]
        outliers_inferiores = volumenes_diarios[volumenes_diarios < Q1 - 1.5 * IQR]
        
        estadisticas_volumen.update({
            'outliers_superiores': len(outliers_superiores),
            'outliers_inferiores': len(outliers_inferiores),
            'fechas_outliers_sup': outliers_superiores.index.tolist(),
            'fechas_outliers_inf': outliers_inferiores.index.tolist()
        })
        
        print(f"📈 ANÁLISIS DE VOLÚMENES DIARIOS:")
        print(f"   Promedio: {estadisticas_volumen['promedio_diario']:.1f} llamadas/día")
        print(f"   Coef. Variación: {estadisticas_volumen['coeficiente_variacion']:.3f}")
        print(f"   Días con outliers: {estadisticas_volumen['outliers_superiores'] + estadisticas_volumen['outliers_inferiores']}")
        
        return estadisticas_volumen, volumenes_diarios
    
    def detectar_patrones_estacionales(self):
        """Detecta patrones estacionales específicos del call center"""
        
        if 'fecha_procesada' not in self.df.columns:
            print("❌ Ejecutar analizar_volumenes_diarios() primero")
            return None
        
        df_temporal = self.df[self.df['fecha_procesada'].dt.dayofweek < 5].copy()
        df_temporal['hora'] = df_temporal['fecha_procesada'].dt.hour
        df_temporal['dia_semana'] = df_temporal['fecha_procesada'].dt.day_name()
        df_temporal['dia_mes'] = df_temporal['fecha_procesada'].dt.day
        df_temporal['semana_ano'] = df_temporal['fecha_procesada'].dt.isocalendar().week
        
        patrones = {
            'por_hora': df_temporal.groupby('hora').size(),
            'por_dia_semana': df_temporal.groupby('dia_semana').size(),
            'por_dia_mes': df_temporal.groupby('dia_mes').size(),
            'por_semana': df_temporal.groupby('semana_ano').size()
        }
        
        # Detectar horas pico
        horas_pico = patrones['por_hora'].nlargest(3)
        horas_valle = patrones['por_hora'].nsmallest(3)
        
        # Detectar días más ocupados
        dias_ocupados = patrones['por_dia_semana'].nlargest(3)
        
        resultado_patrones = {
            'horas_pico': horas_pico.to_dict(),
            'horas_valle': horas_valle.to_dict(),
            'dias_mas_ocupados': dias_ocupados.to_dict(),
            'variabilidad_horaria': patrones['por_hora'].std() / patrones['por_hora'].mean(),
            'variabilidad_semanal': patrones['por_dia_semana'].std() / patrones['por_dia_semana'].mean()
        }
        
        print(f"🕐 PATRONES ESTACIONALES DETECTADOS:")
        print(f"   Horas pico: {list(horas_pico.index)}")
        print(f"   Días más ocupados: {list(dias_ocupados.index)}")
        
        return resultado_patrones, patrones
    
    def analizar_calidad_datos(self):
        """Evaluación completa de calidad de datos"""
        
        calidad = {
            'completitud': {},
            'consistencia': {},
            'precision': {},
            'validez': {}
        }
        
        # Completitud - valores nulos
        for col in self.df.columns:
            nulos = self.df[col].isnull().sum()
            porcentaje_nulos = (nulos / len(self.df)) * 100
            calidad['completitud'][col] = {
                'valores_nulos': nulos,
                'porcentaje_nulos': porcentaje_nulos,
                'completitud_score': 100 - porcentaje_nulos
            }
        
        # Consistencia - duplicados
        duplicados_totales = self.df.duplicated().sum()
        calidad['consistencia']['duplicados_completos'] = duplicados_totales
        
        # Precisión - detección de anomalías
        columnas_numericas = self.df.select_dtypes(include=[np.number]).columns
        for col in columnas_numericas:
            valores_negativos = (self.df[col] < 0).sum()
            valores_cero = (self.df[col] == 0).sum()
            calidad['precision'][col] = {
                'valores_negativos': valores_negativos,
                'valores_cero': valores_cero,
                'outliers_z_score': self._detectar_outliers_zscore(self.df[col])
            }
        
        # Score general de calidad
        scores_completitud = [v['completitud_score'] for v in calidad['completitud'].values()]
        score_general = np.mean(scores_completitud)
        
        print(f"🏆 SCORE GENERAL DE CALIDAD: {score_general:.1f}/100")
        
        return calidad
    
    def _detectar_outliers_zscore(self, serie, umbral=3):
        """Detecta outliers usando Z-score"""
        if serie.dtype in ['object', 'datetime64[ns]']:
            return 0
        
        try:
            z_scores = np.abs((serie - serie.mean()) / serie.std())
            return (z_scores > umbral).sum()
        except:
            return 0
    
    def generar_reporte_diagnostico(self, output_path):
        """Genera reporte completo de diagnóstico"""
        
        print("📝 GENERANDO REPORTE DE DIAGNÓSTICO...")
        
        # Ejecutar todos los análisis
        estructura_temporal = self.analizar_estructura_temporal()
        direcciones, telefonos = self.detectar_llamadas_entrantes_salientes()
        volumenes_stats, volumenes_serie = self.analizar_volumenes_diarios()
        patrones_est, patrones_datos = self.detectar_patrones_estacionales()
        calidad_datos = self.analizar_calidad_datos()
        
        # Compilar reporte
        reporte_completo = {
            'metadata': {
                'fecha_analisis': datetime.now().isoformat(),
                'total_registros': len(self.df),
                'periodo_datos': estructura_temporal,
                'columnas_detectadas': {
                    'fecha': list(estructura_temporal.keys()),
                    'direccion': direcciones,
                    'telefono': telefonos
                }
            },
            'calidad_datos': calidad_datos,
            'volumenes_diarios': volumenes_stats,
            'patrones_estacionales': patrones_est,
            'recomendaciones': self._generar_recomendaciones(calidad_datos, volumenes_stats, patrones_est)
        }
        
        # Guardar reporte
        with open(f"{output_path}/diagnostico_llamadas_alodesk.json", 'w', encoding='utf-8') as f:
            json.dump(reporte_completo, f, indent=2, ensure_ascii=False, default=str)
        
        # Generar CSV con datos procesados para análisis
        if 'fecha_procesada' in self.df.columns:
            df_procesado = self.df.copy()
            df_procesado['fecha_str'] = df_procesado['fecha_procesada'].dt.date
            df_procesado['hora'] = df_procesado['fecha_procesada'].dt.hour
            df_procesado['dia_semana'] = df_procesado['fecha_procesada'].dt.day_name()
            
            df_procesado.to_csv(f"{output_path}/datos_llamadas_procesados.csv", index=False, encoding='utf-8-sig')
        
        print(f"✅ Reporte guardado en {output_path}")
        return reporte_completo
    
    def _generar_recomendaciones(self, calidad, volumenes, patrones):
        """Genera recomendaciones específicas para mejorar predicciones"""
        
        recomendaciones = []
        
        # Recomendaciones por calidad de datos
        score_promedio = np.mean([v['completitud_score'] for v in calidad['completitud'].values()])
        if score_promedio < 80:
            recomendaciones.append({
                'tipo': 'CALIDAD_DATOS',
                'prioridad': 'ALTA',
                'problema': f'Calidad de datos baja ({score_promedio:.1f}/100)',
                'solucion': 'Implementar validación de datos en origen y limpieza automatizada'
            })
        
        # Recomendaciones por variabilidad
        if volumenes and volumenes['coeficiente_variacion'] > 0.5:
            recomendaciones.append({
                'tipo': 'VARIABILIDAD',
                'prioridad': 'ALTA',
                'problema': f'Alta variabilidad diaria ({volumenes["coeficiente_variacion"]:.3f})',
                'solucion': 'Usar modelos que manejen bien la variabilidad (ARIMA, ensemble methods)'
            })
        
        # Recomendaciones por outliers
        if volumenes and (volumenes['outliers_superiores'] + volumenes['outliers_inferiores']) > 5:
            recomendaciones.append({
                'tipo': 'OUTLIERS',
                'prioridad': 'MEDIA',
                'problema': 'Múltiples días con volúmenes atípicos',
                'solucion': 'Implementar detección y tratamiento automático de outliers'
            })
        
        # Recomendaciones por patrones estacionales
        if patrones and patrones['variabilidad_horaria'] > 0.8:
            recomendaciones.append({
                'tipo': 'ESTACIONALIDAD',
                'prioridad': 'ALTA',
                'problema': 'Fuerte patrón horario no capturado',
                'solucion': 'Agregar regresores horarios y usar modelos con estacionalidad múltiple'
            })
        
        return recomendaciones

def main():
    """Función principal de auditoría"""
    
    # Usar directorio actual del script
    from pathlib import Path
    base_path = Path(__file__).parent.absolute()
    archivo_llamadas = base_path / "backups" / "alodesk_reporte_llamadas_jan2023_to_jul2025.csv"
    output_path = base_path
    
    print("🔍 INICIANDO AUDITORÍA PROFUNDA DE DATOS DE LLAMADAS")
    print("=" * 60)
    
    # Crear auditor
    auditor = AuditoriaLlamadasAlodesk(archivo_llamadas)
    
    # Ejecutar auditoría completa
    if auditor.cargar_y_limpiar_datos():
        reporte = auditor.generar_reporte_diagnostico(output_path)
        
        print("\n🎯 RESUMEN EJECUTIVO:")
        print(f"   📊 Total registros: {len(auditor.df)}")
        
        if 'recomendaciones' in reporte:
            print(f"   ⚠️ Recomendaciones: {len(reporte['recomendaciones'])}")
            
            for rec in reporte['recomendaciones']:
                print(f"   🔧 {rec['tipo']}: {rec['problema']}")
        
        print(f"\n📄 Reporte completo disponible en: {output_path}")
        
    else:
        print("❌ No se pudo completar la auditoría")

if __name__ == "__main__":
    main()
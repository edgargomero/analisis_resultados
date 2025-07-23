#!/usr/bin/env python3
"""
CEAPSI - Sistema de Segmentación de Llamadas Alodesk
Separación inteligente de llamadas entrantes vs salientes
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import re

class SegmentadorLlamadasAlodesk:
    """Segmentador inteligente para llamadas entrantes vs salientes"""
    
    def __init__(self, datos_llamadas_path):
        self.datos_path = datos_llamadas_path
        self.df = None
        self.segmentacion_reglas = {}
        
    def cargar_datos_llamadas(self):
        """Carga datos de llamadas con validación"""
        try:
            self.df = pd.read_csv(self.datos_path, sep=';', encoding='utf-8')
            print(f"✅ Cargadas {len(self.df)} llamadas")
            print(f"📋 Columnas disponibles: {list(self.df.columns)}")
            return True
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def detectar_direccion_llamada(self):
        """Detecta automáticamente la dirección de las llamadas"""
        
        # Tu archivo tiene la columna SENTIDO con valores 'in' y 'out'
        columnas_direccion = ['SENTIDO']
        
        print(f"🔍 Columnas de dirección detectadas: {columnas_direccion}")
        
        # Analizar valores en la columna SENTIDO
        reglas_detectadas = {}
        
        if 'SENTIDO' in self.df.columns:
            valores_unicos = self.df['SENTIDO'].value_counts()
            print(f"📊 SENTIDO: {valores_unicos.to_dict()}")
            
            # Crear reglas específicas para tu archivo
            reglas_detectadas['SENTIDO'] = {
                'entrantes': ['in'],  # llamadas entrantes
                'salientes': ['out']  # llamadas salientes
            }
            
            print(f"🔧 Reglas configuradas: entrantes={reglas_detectadas['SENTIDO']['entrantes']}, salientes={reglas_detectadas['SENTIDO']['salientes']}")
        
        self.segmentacion_reglas = reglas_detectadas
        return reglas_detectadas
    
    def segmentar_por_numero_telefono(self):
        """Segmenta usando patrones en números de teléfono"""
        
        # Buscar columnas de números de teléfono
        columnas_telefono = []
        for col in self.df.columns:
            col_lower = col.lower().strip()
            if any(palabra in col_lower for palabra in 
                   ['telefono', 'numero', 'phone', 'caller', 'called']):
                columnas_telefono.append(col)
        
        print(f"📱 Columnas de teléfono: {columnas_telefono}")
        
        # Analizar patrones de números
        patrones_telefono = {}
        
        for col in columnas_telefono:
            if self.df[col].dtype == 'object':
                numeros_limpios = self.df[col].astype(str).str.extract(r'(\d+)')
                longitudes = numeros_limpios[0].str.len()
                
                # Estadísticas de longitudes
                stats_longitud = {
                    'promedio': longitudes.mean(),
                    'moda': longitudes.mode().iloc[0] if not longitudes.mode().empty else None,
                    'distribucion': longitudes.value_counts().head(10).to_dict()
                }
                
                patrones_telefono[col] = stats_longitud
                print(f"📊 {col} - Longitud promedio: {stats_longitud['promedio']:.1f}")
        
        return patrones_telefono
    
    def segmentar_por_horarios(self):
        """Segmenta usando patrones horarios típicos de call center"""
        
        # Usar la columna FECHA de tu archivo
        col_fecha = 'FECHA'
        
        if col_fecha not in self.df.columns:
            print("⚠️ No se encontró la columna FECHA")
            return None
        
        try:
            # Convertir a datetime usando el formato específico
            fechas = pd.to_datetime(self.df[col_fecha], format='%d-%m-%Y %H:%M:%S')
            self.df['hora'] = fechas.dt.hour
            self.df['dia_semana'] = fechas.dt.day_name()
            
            # Análisis de patrones horarios
            distribucion_horaria = self.df['hora'].value_counts().sort_index()
            
            # Definir horarios típicos
            horarios_comerciales = list(range(8, 18))  # 8 AM - 6 PM
            horarios_seguimiento = list(range(18, 20))  # 6 PM - 8 PM (salientes típicos)
            
            # Segmentar por probabilidades
            self.df['prob_entrante'] = self.df['hora'].map(
                lambda h: 0.8 if h in horarios_comerciales 
                         else 0.3 if h in horarios_seguimiento 
                         else 0.1
            )
            
            self.df['prob_saliente'] = 1 - self.df['prob_entrante']
            
            patrones_horarios = {
                'distribucion_por_hora': distribucion_horaria.to_dict(),
                'pico_llamadas': distribucion_horaria.idxmax(),
                'valle_llamadas': distribucion_horaria.idxmin(),
                'horarios_comerciales_pct': (
                    self.df[self.df['hora'].isin(horarios_comerciales)].shape[0] / 
                    len(self.df) * 100
                )
            }
            
            print(f"🕐 Pico de llamadas: {patrones_horarios['pico_llamadas']}:00")
            print(f"📊 Horario comercial: {patrones_horarios['horarios_comerciales_pct']:.1f}%")
            
            return patrones_horarios
            
        except Exception as e:
            print(f"❌ Error en análisis horario: {e}")
            return None
    
    def aplicar_segmentacion_inteligente(self):
        """Aplica segmentación usando todos los métodos disponibles"""
        
        print("🧠 APLICANDO SEGMENTACIÓN INTELIGENTE")
        
        # Ejecutar todos los métodos de detección
        reglas_direccion = self.detectar_direccion_llamada()
        patrones_telefono = self.segmentar_por_numero_telefono()
        patrones_horarios = self.segmentar_por_horarios()
        
        # Crear columna de segmentación combinada
        self.df['tipo_llamada'] = 'INDETERMINADA'
        self.df['confianza_segmentacion'] = 0.0
        
        # Aplicar reglas de dirección (mayor peso)
        for col, reglas in reglas_direccion.items():
            if reglas['entrantes']:
                mask_entrantes = self.df[col].isin(reglas['entrantes'])
                self.df.loc[mask_entrantes, 'tipo_llamada'] = 'ENTRANTE'
                self.df.loc[mask_entrantes, 'confianza_segmentacion'] = 0.9
            
            if reglas['salientes']:
                mask_salientes = self.df[col].isin(reglas['salientes'])
                self.df.loc[mask_salientes, 'tipo_llamada'] = 'SALIENTE'
                self.df.loc[mask_salientes, 'confianza_segmentacion'] = 0.9
        
        # Aplicar reglas horarias para llamadas indeterminadas
        mask_indeterminadas = self.df['tipo_llamada'] == 'INDETERMINADA'
        
        if 'prob_entrante' in self.df.columns:
            # Usar probabilidades horarias
            mask_prob_entrante = mask_indeterminadas & (self.df['prob_entrante'] > 0.6)
            mask_prob_saliente = mask_indeterminadas & (self.df['prob_saliente'] > 0.6)
            
            self.df.loc[mask_prob_entrante, 'tipo_llamada'] = 'ENTRANTE'
            self.df.loc[mask_prob_entrante, 'confianza_segmentacion'] = self.df.loc[mask_prob_entrante, 'prob_entrante']
            
            self.df.loc[mask_prob_saliente, 'tipo_llamada'] = 'SALIENTE'
            self.df.loc[mask_prob_saliente, 'confianza_segmentacion'] = self.df.loc[mask_prob_saliente, 'prob_saliente']
        
        # Estadísticas finales
        distribucion_final = self.df['tipo_llamada'].value_counts()
        confianza_promedio = self.df[self.df['tipo_llamada'] != 'INDETERMINADA']['confianza_segmentacion'].mean()
        
        print(f"📊 RESULTADO DE SEGMENTACIÓN:")
        for tipo, cantidad in distribucion_final.items():
            porcentaje = (cantidad / len(self.df)) * 100
            print(f"   {tipo}: {cantidad} llamadas ({porcentaje:.1f}%)")
        
        print(f"🎯 Confianza promedio: {confianza_promedio:.2f}")
        
        return distribucion_final, confianza_promedio
    
    def generar_datasets_segmentados(self, output_path):
        """Genera datasets separados por tipo de llamada"""
        
        if 'tipo_llamada' not in self.df.columns:
            print("❌ Ejecutar aplicar_segmentacion_inteligente() primero")
            return False
        
        # Filtrar solo días laborales
        if 'dia_semana' in self.df.columns:
            dias_laborales = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            df_laborales = self.df[self.df['dia_semana'].isin(dias_laborales)].copy()
        else:
            df_laborales = self.df.copy()
        
        # Generar datasets por tipo
        for tipo_llamada in ['ENTRANTE', 'SALIENTE']:
            df_tipo = df_laborales[df_laborales['tipo_llamada'] == tipo_llamada].copy()
            
            if len(df_tipo) > 0:
                # Agregar por día para forecasting
                if 'hora' in df_tipo.columns:
                    # Usar la columna FECHA ya procesada
                    df_tipo['fecha'] = pd.to_datetime(df_tipo['FECHA'], format='%d-%m-%Y %H:%M:%S').dt.date
                    
                    # Dataset diario agregado
                    df_diario = df_tipo.groupby('fecha').agg({
                        'tipo_llamada': 'count',
                        'confianza_segmentacion': 'mean'
                    }).reset_index()
                    
                    df_diario.columns = ['ds', 'y', 'confianza_promedio']
                    df_diario['ds'] = pd.to_datetime(df_diario['ds'])
                    
                    # Agregar regresores básicos
                    df_diario['dia_semana'] = df_diario['ds'].dt.dayofweek + 1
                    df_diario['es_inicio_mes'] = (df_diario['ds'].dt.day <= 5).astype(int)
                    df_diario['semana_mes'] = ((df_diario['ds'].dt.day - 1) // 7) + 1
                    
                    # Guardar dataset para Prophet
                    filename_prophet = f"{output_path}/datos_prophet_{tipo_llamada.lower()}.csv"
                    df_diario.to_csv(filename_prophet, index=False)
                    
                    print(f"✅ Dataset {tipo_llamada}: {len(df_diario)} días → {filename_prophet}")
                
                # Guardar dataset completo
                filename_completo = f"{output_path}/llamadas_{tipo_llamada.lower()}_completo.csv"
                df_tipo.to_csv(filename_completo, index=False, encoding='utf-8-sig')
        
        # Dataset combinado con flag de tipo
        if 'fecha' in df_laborales.columns:
            df_combinado_diario = df_laborales.groupby(['fecha', 'tipo_llamada']).size().unstack(fill_value=0).reset_index()
            df_combinado_diario['total_llamadas'] = df_combinado_diario.sum(axis=1, numeric_only=True)
            df_combinado_diario.to_csv(f"{output_path}/llamadas_diario_segmentado.csv", index=False)
        
        return True
    
    def generar_reporte_segmentacion(self, output_path):
        """Genera reporte completo de segmentación"""
        
        reporte = {
            'metadata': {
                'fecha_analisis': datetime.now().isoformat(),
                'total_llamadas': len(self.df),
                'metodo_segmentacion': 'inteligente_multicriterio'
            },
            'distribucion_tipos': self.df['tipo_llamada'].value_counts().to_dict(),
            'estadisticas_confianza': {
                'promedio': float(self.df['confianza_segmentacion'].mean()),
                'mediana': float(self.df['confianza_segmentacion'].median()),
                'alta_confianza': int((self.df['confianza_segmentacion'] > 0.8).sum()),
                'baja_confianza': int((self.df['confianza_segmentacion'] < 0.5).sum())
            },
            'reglas_aplicadas': self.segmentacion_reglas,
            'recomendaciones': self._generar_recomendaciones_segmentacion()
        }
        
        # Agregar análisis temporal si disponible
        if 'hora' in self.df.columns:
            reporte['patrones_temporales'] = {
                'entrantes_por_hora': self.df[self.df['tipo_llamada'] == 'ENTRANTE']['hora'].value_counts().sort_index().to_dict(),
                'salientes_por_hora': self.df[self.df['tipo_llamada'] == 'SALIENTE']['hora'].value_counts().sort_index().to_dict()
            }
        
        # Guardar reporte
        with open(f"{output_path}/reporte_segmentacion_llamadas.json", 'w', encoding='utf-8') as f:
            json.dump(reporte, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Reporte guardado: {output_path}/reporte_segmentacion_llamadas.json")
        return reporte
    
    def _generar_recomendaciones_segmentacion(self):
        """Genera recomendaciones para mejorar la segmentación"""
        
        recomendaciones = []
        
        # Análisis de confianza
        indeterminadas = (self.df['tipo_llamada'] == 'INDETERMINADA').sum()
        pct_indeterminadas = (indeterminadas / len(self.df)) * 100
        
        if pct_indeterminadas > 20:
            recomendaciones.append({
                'tipo': 'SEGMENTACION',
                'prioridad': 'ALTA',
                'problema': f'{pct_indeterminadas:.1f}% de llamadas sin clasificar',
                'solucion': 'Revisar campos adicionales en Alodesk para mejorar clasificación'
            })
        
        # Análisis de balance
        if 'tipo_llamada' in self.df.columns:
            tipos_count = self.df['tipo_llamada'].value_counts()
            if len(tipos_count) >= 2:
                ratio_entrantes_salientes = tipos_count.get('ENTRANTE', 0) / max(1, tipos_count.get('SALIENTE', 1))
                
                if ratio_entrantes_salientes > 5 or ratio_entrantes_salientes < 0.2:
                    recomendaciones.append({
                        'tipo': 'BALANCE',
                        'prioridad': 'MEDIA',
                        'problema': f'Desbalance entre tipos: ratio {ratio_entrantes_salientes:.1f}',
                        'solucion': 'Crear modelos separados para cada tipo de llamada'
                    })
        
        # Análisis de confianza promedio
        confianza_promedio = self.df['confianza_segmentacion'].mean()
        if confianza_promedio < 0.7:
            recomendaciones.append({
                'tipo': 'CONFIANZA',
                'prioridad': 'ALTA',
                'problema': f'Confianza de segmentación baja ({confianza_promedio:.2f})',
                'solucion': 'Validar manualmente una muestra y ajustar reglas de clasificación'
            })
        
        return recomendaciones

def main():
    """Función principal de segmentación"""
    
    # Usar directorio actual del script  
    from pathlib import Path
    base_path = Path(__file__).parent.absolute()
    archivo_llamadas = base_path / "backups" / "alodesk_reporte_llamadas_jan2023_to_jul2025.csv" 
    output_path = base_path
    
    print("🔀 INICIANDO SEGMENTACIÓN INTELIGENTE DE LLAMADAS")
    print("=" * 60)
    
    # Crear segmentador
    segmentador = SegmentadorLlamadasAlodesk(archivo_llamadas)
    
    # Ejecutar segmentación completa
    if segmentador.cargar_datos_llamadas():
        
        # Aplicar segmentación
        distribucion, confianza = segmentador.aplicar_segmentacion_inteligente()
        
        # Generar datasets
        if segmentador.generar_datasets_segmentados(output_path):
            print("✅ Datasets segmentados generados")
        
        # Generar reporte
        reporte = segmentador.generar_reporte_segmentacion(output_path)
        
        print("\n🎯 RESUMEN EJECUTIVO DE SEGMENTACIÓN:")
        print(f"   📊 Total llamadas procesadas: {len(segmentador.df)}")
        print(f"   🎯 Confianza promedio: {confianza:.2f}")
        
        for tipo, cantidad in distribucion.items():
            porcentaje = (cantidad / len(segmentador.df)) * 100
            print(f"   📞 {tipo}: {cantidad} ({porcentaje:.1f}%)")
        
        print(f"\n📁 Archivos generados en: {output_path}")
        
    else:
        print("❌ No se pudo completar la segmentación")

if __name__ == "__main__":
    main()
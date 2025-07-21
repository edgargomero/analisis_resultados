#!/usr/bin/env python3
"""
CEAPSI Forecasting - Generación de Predicciones
Sistema automatizado para generar predicciones semanales
"""

import pandas as pd
import numpy as np
import json
import pickle
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')
import os

# Ruta base donde están las carpetas de resultados
base_resultados = r"C:\Users\edgar\OneDrive\Documentos\BBDD CEAPSI\claude\analisis_resultados"

# Buscar todas las subcarpetas que empiecen con 'resultados_'
subcarpetas = [d for d in os.listdir(base_resultados) if d.startswith('resultados_') and os.path.isdir(os.path.join(base_resultados, d))]
if not subcarpetas:
    raise FileNotFoundError("No se encontraron carpetas de resultados en 'analisis_resultados'.")

# Ordenar por nombre (timestamp) y tomar la más reciente
subcarpetas.sort()
ultima_carpeta = subcarpetas[-1]
ruta_ultima = os.path.join(base_resultados, ultima_carpeta)

# Rutas a los archivos más recientes
modelo_path = os.path.join(ruta_ultima, "modelo_prophet.pkl")
metadatos_path = os.path.join(ruta_ultima, "metadatos_modelo.json")
print(f"📂 Usando modelo Prophet de: {modelo_path}")

class CeapsiPredictionEngine:
    """Motor de predicciones automatizado para CEAPSI"""
    
    def __init__(self, modelo_path, metadatos_path):
        self.modelo_path = modelo_path
        self.metadatos_path = metadatos_path
        self.model = None
        self.metadatos = {}
        self.predicciones = None
        
    def cargar_modelo(self):
        """Carga modelo Prophet entrenado"""
        try:
            with open(self.modelo_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(self.metadatos_path, 'r', encoding='utf-8') as f:
                self.metadatos = json.load(f)
            
            print(f"✅ Modelo cargado:")
            print(f"   📅 Entrenado: {self.metadatos['fecha_entrenamiento']}")
            print(f"   🔧 Regresores: {len(self.metadatos['regresores_utilizados'])}")
            print(f"   📊 Componentes: {len(self.metadatos['componentes_modelo'])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            return False
    
    def obtener_datos_actuales(self):
        """Obtiene datos más recientes para predicciones"""
        # En producción, esto conectaría a las bases de datos reales
        # Por ahora, simulamos datos actuales basados en patrones históricos
        
        print("📊 Obteniendo datos actuales...")
        
        # Simular datos de última semana
        fecha_fin = datetime.now().date()
        fecha_inicio = fecha_fin - timedelta(days=7)
        
        # Generar datos simulados realistas
        datos_actuales = []
        for i in range(7):
            fecha = fecha_inicio + timedelta(days=i)
            if fecha.weekday() < 6:  # Solo días laborales
                
                # Simular volúmenes basados en día de semana
                factor_dia = {0: 1.2, 1: 1.3, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.7}[fecha.weekday()]
                
                datos_actuales.append({
                    'fecha': fecha,
                    'volumen_reservas': int(12 * factor_dia + np.random.normal(0, 2)),
                    'volumen_conversaciones': int(25 * factor_dia + np.random.normal(0, 3)),
                    'volumen_llamadas': int(35 * factor_dia + np.random.normal(0, 4)),
                    'profesionales_disponibles': 8
                })
        
        df_actuales = pd.DataFrame(datos_actuales)
        
        print(f"   📈 Datos obtenidos para {len(df_actuales)} días")
        print(f"   📅 Período: {df_actuales['fecha'].min()} a {df_actuales['fecha'].max()}")
        
        return df_actuales
    
    def estimar_regresores_futuros(self, dias_futuros=28):
        """Estima valores de regresores para días futuros"""
        
        print(f"🔮 Estimando regresores para {dias_futuros} días futuros...")
        
        # Obtener datos actuales para calibrar estimaciones
        datos_actuales = self.obtener_datos_actuales()
        
        # Generar fechas futuras (solo días laborales)
        fecha_inicio = datetime.now().date() + timedelta(days=1)
        fechas_futuras = []
        fecha_actual = fecha_inicio
        
        while len(fechas_futuras) < dias_futuros:
            if fecha_actual.weekday() < 6:  # Lunes a sábado
                fechas_futuras.append(fecha_actual)
            fecha_actual += timedelta(days=1)
        
        # Estimar regresores
        regresores_futuros = []
        
        for fecha in fechas_futuras:
            # Factores estacionales por día de semana
            factor_dia = {0: 1.2, 1: 1.3, 2: 1.1, 3: 1.0, 4: 0.9, 5: 0.7}[fecha.weekday()]
            
            # Factor estacional por semana del mes
            semana_mes = ((fecha.day - 1) // 7) + 1
            factor_semana = {1: 1.1, 2: 1.0, 3: 0.95, 4: 1.05}.get(semana_mes, 1.0)
            
            # Promedios base de datos actuales
            vol_reservas_base = datos_actuales['volumen_reservas'].mean()
            vol_conversaciones_base = datos_actuales['volumen_conversaciones'].mean()
            vol_llamadas_base = datos_actuales['volumen_llamadas'].mean()
            
            # Aplicar factores estacionales con algo de variabilidad
            regresores_futuros.append({
                'ds': fecha,
                'volumen_reservas': max(1, int(vol_reservas_base * factor_dia * factor_semana + np.random.normal(0, 1))),
                'volumen_conversaciones': max(1, int(vol_conversaciones_base * factor_dia * factor_semana + np.random.normal(0, 2))),
                'volumen_llamadas': max(1, int(vol_llamadas_base * factor_dia * factor_semana + np.random.normal(0, 2))),
                'dia_semana': fecha.weekday() + 1,
                'es_inicio_mes': 1 if fecha.day <= 5 else 0,
                'profesionales_disponibles': 8,  # Asumir disponibilidad estándar
            })
            
            # Agregar regresores de porcentaje si existen en el modelo
            for regresor in self.metadatos.get('regresores_utilizados', []):
                if regresor.startswith('pct_') and regresor not in regresores_futuros[-1]:
                    # Usar distribución histórica promedio
                    regresores_futuros[-1][regresor] = 0.3  # Valor por defecto
        
        df_regresores = pd.DataFrame(regresores_futuros)
        df_regresores['ds'] = pd.to_datetime(df_regresores['ds'])
        
        print(f"   ✅ Regresores estimados para {len(df_regresores)} días")
        
        return df_regresores
    
    def generar_predicciones_automaticas(self, dias_futuros=28):
        """Genera predicciones automáticas para los próximos días"""
        
        if self.model is None:
            print("❌ Modelo no cargado")
            return None
        
        try:
            print(f"🚀 Generando predicciones automáticas para {dias_futuros} días...")
            
            # Crear DataFrame futuro
            future = self.model.make_future_dataframe(
                periods=dias_futuros + 7,  # Margen adicional
                freq='D'
            )
            
            # Filtrar solo días laborales
            future = future[future['ds'].dt.dayofweek < 6].reset_index(drop=True)
            
            # Obtener regresores futuros
            df_regresores = self.estimar_regresores_futuros(dias_futuros)
            
            # Combinar con future dataframe
            future = future.merge(df_regresores, on='ds', how='left')
            
            # Rellenar valores faltantes con promedios
            for regresor in self.metadatos.get('regresores_utilizados', []):
                if regresor in future.columns:
                    future[regresor] = future[regresor].fillna(future[regresor].mean())
            
            # Generar predicciones
            forecast = self.model.predict(future)
            
            # Filtrar solo predicciones futuras
            fecha_corte = datetime.now().date()
            predicciones_futuras = forecast[forecast['ds'].dt.date > fecha_corte].head(dias_futuros)
            
            self.predicciones = predicciones_futuras
            
            print(f"✅ Predicciones generadas:")
            print(f"   📅 Período: {predicciones_futuras['ds'].min().date()} a {predicciones_futuras['ds'].max().date()}")
            print(f"   📊 Días: {len(predicciones_futuras)}")
            print(f"   🎯 Promedio: {predicciones_futuras['yhat'].mean():.1f} horas/día")
            print(f"   📈 Rango: {predicciones_futuras['yhat'].min():.1f} - {predicciones_futuras['yhat'].max():.1f} horas")
            
            return predicciones_futuras
            
        except Exception as e:
            print(f"❌ Error generando predicciones: {e}")
            return None
    
    def detectar_alertas(self, predicciones):
        """Detecta alertas automáticas basadas en predicciones"""
        
        if predicciones is None or len(predicciones) == 0:
            return []
        
        print("🚨 Detectando alertas automáticas...")
        
        alertas = []
        
        # Umbrales de alerta
        umbral_alto = 50  # horas
        umbral_muy_alto = 60  # horas
        umbral_bajo = 25  # horas
        
        for idx, row in predicciones.iterrows():
            fecha = row['ds'].date()
            dia_semana = row['ds'].strftime('%A')
            horas = row['yhat']
            limite_superior = row['yhat_upper']
            
            # Alertas por demanda alta
            if horas > umbral_muy_alto:
                alertas.append({
                    'tipo': 'CRITICA',
                    'fecha': fecha.isoformat(),
                    'dia_semana': dia_semana,
                    'horas_predichas': round(horas, 1),
                    'mensaje': f'Demanda crítica: {horas:.1f}h. Requiere personal adicional urgente.',
                    'accion': 'Activar protocolo de personal de emergencia',
                    'prioridad': 1
                })
            elif horas > umbral_alto:
                alertas.append({
                    'tipo': 'ALTA',
                    'fecha': fecha.isoformat(),
                    'dia_semana': dia_semana,
                    'horas_predichas': round(horas, 1),
                    'mensaje': f'Demanda alta: {horas:.1f}h. Considerar personal adicional.',
                    'accion': 'Programar turnos extra o personal de refuerzo',
                    'prioridad': 2
                })
            
            # Alertas por demanda baja (posible sobredotación)
            elif horas < umbral_bajo:
                alertas.append({
                    'tipo': 'BAJA',
                    'fecha': fecha.isoformat(),
                    'dia_semana': dia_semana,
                    'horas_predichas': round(horas, 1),
                    'mensaje': f'Demanda baja: {horas:.1f}h. Evaluar reducción de personal.',
                    'accion': 'Considerar turnos reducidos o reasignación',
                    'prioridad': 3
                })
            
            # Alertas por alta incertidumbre
            incertidumbre = limite_superior - horas
            if incertidumbre > 15:  # Alta variabilidad
                alertas.append({
                    'tipo': 'INCERTIDUMBRE',
                    'fecha': fecha.isoformat(),
                    'dia_semana': dia_semana,
                    'horas_predichas': round(horas, 1),
                    'mensaje': f'Alta incertidumbre: ±{incertidumbre:.1f}h. Monitorear de cerca.',
                    'accion': 'Preparar personal de contingencia',
                    'prioridad': 3
                })
        
        # Alertas por patrones semanales
        if len(predicciones) >= 7:
            promedio_semanal = predicciones.head(7)['yhat'].mean()
            if promedio_semanal > 45:
                alertas.append({
                    'tipo': 'PATRON_SEMANAL',
                    'fecha': predicciones.iloc[0]['ds'].date().isoformat(),
                    'dia_semana': 'Toda la semana',
                    'horas_predichas': round(promedio_semanal, 1),
                    'mensaje': f'Semana de alta demanda: {promedio_semanal:.1f}h promedio.',
                    'accion': 'Planificar recursos adicionales para toda la semana',
                    'prioridad': 2
                })
        
        print(f"   🚨 {len(alertas)} alertas detectadas")
        
        # Ordenar por prioridad
        alertas.sort(key=lambda x: x['prioridad'])
        
        return alertas
    
    def generar_recomendaciones_staffing(self, predicciones):
        """Genera recomendaciones específicas de staffing"""
        
        if predicciones is None or len(predicciones) == 0:
            return []
        
        print("💡 Generando recomendaciones de staffing...")
        
        recomendaciones = []
        
        for idx, row in predicciones.iterrows():
            fecha = row['ds'].date()
            dia_semana = row['ds'].strftime('%A')
            horas = row['yhat']
            limite_inferior = row['yhat_lower']
            limite_superior = row['yhat_upper']
            
            # Calcular personal necesario (asumiendo 8h por persona)
            personal_minimo = max(3, int(np.ceil(limite_inferior / 8)))
            personal_optimo = max(4, int(np.ceil(horas / 8)))
            personal_maximo = int(np.ceil(limite_superior / 8))
            
            # Determinar tipo de día
            if dia_semana in ['Monday', 'Tuesday', 'Wednesday']:
                tipo_dia = 'Alto tráfico'
                factor_secretarias = 1.2
            elif dia_semana in ['Thursday', 'Friday']:
                tipo_dia = 'Tráfico medio'
                factor_secretarias = 1.0
            else:  # Saturday
                tipo_dia = 'Tráfico reducido'
                factor_secretarias = 0.8
            
            # Calcular dotación por área
            secretarias_call_center = max(2, int(personal_optimo * 0.4 * factor_secretarias))
            profesionales = max(2, int(personal_optimo * 0.6))
            
            recomendacion = {
                'fecha': fecha.isoformat(),
                'dia_semana': dia_semana,
                'tipo_dia': tipo_dia,
                'horas_predichas': round(horas, 1),
                'personal_total': {
                    'minimo': personal_minimo,
                    'optimo': personal_optimo,
                    'maximo': personal_maximo
                },
                'dotacion_detallada': {
                    'call_center_secretarias': secretarias_call_center,
                    'profesionales_medicos': profesionales,
                    'personal_apoyo': max(1, personal_optimo - secretarias_call_center - profesionales)
                },
                'turnos_sugeridos': self._calcular_turnos_sugeridos(horas, dia_semana),
                'observaciones': self._generar_observaciones(horas, dia_semana, limite_superior - limite_inferior)
            }
            
            recomendaciones.append(recomendacion)
        
        print(f"   💡 {len(recomendaciones)} recomendaciones generadas")
        
        return recomendaciones
    
    def _calcular_turnos_sugeridos(self, horas_necesarias, dia_semana):
        """Calcula distribución de turnos sugerida"""
        
        if horas_necesarias > 50:
            return {
                'turno_mañana': '08:00-16:00 (personal completo)',
                'turno_tarde': '14:00-20:00 (refuerzo)',
                'turno_sabado': '08:00-14:00' if 'Saturday' in dia_semana else None
            }
        elif horas_necesarias > 35:
            return {
                'turno_mañana': '08:00-16:00 (personal estándar)',
                'turno_tarde': '12:00-18:00 (reducido)',
                'turno_sabado': '08:00-13:00' if 'Saturday' in dia_semana else None
            }
        else:
            return {
                'turno_mañana': '09:00-15:00 (mínimo)',
                'turno_tarde': 'Opcional según demanda',
                'turno_sabado': '09:00-12:00' if 'Saturday' in dia_semana else None
            }
    
    def _generar_observaciones(self, horas, dia_semana, incertidumbre):
        """Genera observaciones específicas para cada día"""
        
        observaciones = []
        
        if 'Monday' in dia_semana:
            observaciones.append("Lunes: Mayor volumen de reservas nuevas")
        elif 'Friday' in dia_semana:
            observaciones.append("Viernes: Posible concentración de consultas")
        elif 'Saturday' in dia_semana:
            observaciones.append("Sábado: Horario reducido, demanda específica")
        
        if horas > 45:
            observaciones.append("Considerar activar protocolo de alta demanda")
        
        if incertidumbre > 10:
            observaciones.append("Alta variabilidad: mantener personal de contingencia")
        
        return observaciones
    
    def exportar_resultados(self, output_path, formato='json'):
        """Exporta resultados en diferentes formatos"""
        
        if self.predicciones is None:
            print("❌ No hay predicciones para exportar")
            return False
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Preparar datos para exportación
            predicciones_export = self.predicciones.copy()
            predicciones_export['ds'] = predicciones_export['ds'].dt.strftime('%Y-%m-%d')
            
            # Generar alertas y recomendaciones
            alertas = self.detectar_alertas(self.predicciones)
            recomendaciones = self.generar_recomendaciones_staffing(self.predicciones)
            
            # Crear estructura de exportación
            export_data = {
                'metadata': {
                    'fecha_generacion': datetime.now().isoformat(),
                    'modelo_version': self.metadatos.get('fecha_entrenamiento', 'unknown'),
                    'horizonte_prediccion': len(predicciones_export),
                    'periodo': f"{predicciones_export['ds'].iloc[0]} a {predicciones_export['ds'].iloc[-1]}"
                },
                'predicciones': predicciones_export[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict('records'),
                'alertas': alertas,
                'recomendaciones_staffing': recomendaciones,
                'resumen_ejecutivo': {
                    'promedio_horas_diarias': float(predicciones_export['yhat'].mean()),
                    'total_horas_periodo': float(predicciones_export['yhat'].sum()),
                    'dia_mayor_demanda': predicciones_export.loc[predicciones_export['yhat'].idxmax(), 'ds'],
                    'horas_dia_pico': float(predicciones_export['yhat'].max()),
                    'total_alertas': len(alertas),
                    'alertas_criticas': len([a for a in alertas if a['tipo'] == 'CRITICA'])
                }
            }
            
            # Exportar según formato
            if formato == 'json':
                filename = f"{output_path}/predicciones_ceapsi_{timestamp}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif formato == 'csv':
                # Exportar predicciones como CSV
                filename = f"{output_path}/predicciones_ceapsi_{timestamp}.csv"
                predicciones_export.to_csv(filename, index=False)
                
                # Exportar alertas como CSV separado
                if alertas:
                    alertas_df = pd.DataFrame(alertas)
                    alertas_filename = f"{output_path}/alertas_ceapsi_{timestamp}.csv"
                    alertas_df.to_csv(alertas_filename, index=False)
            
            elif formato == 'excel':
                filename = f"{output_path}/predicciones_ceapsi_{timestamp}.xlsx"
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    predicciones_export.to_excel(writer, sheet_name='Predicciones', index=False)
                    
                    if alertas:
                        pd.DataFrame(alertas).to_excel(writer, sheet_name='Alertas', index=False)
                    
                    if recomendaciones:
                        # Aplanar recomendaciones para Excel
                        rec_flat = []
                        for rec in recomendaciones:
                            rec_flat.append({
                                'fecha': rec['fecha'],
                                'dia_semana': rec['dia_semana'],
                                'horas_predichas': rec['horas_predichas'],
                                'personal_optimo': rec['personal_total']['optimo'],
                                'call_center': rec['dotacion_detallada']['call_center_secretarias'],
                                'profesionales': rec['dotacion_detallada']['profesionales_medicos']
                            })
                        pd.DataFrame(rec_flat).to_excel(writer, sheet_name='Recomendaciones', index=False)
            
            print(f"✅ Resultados exportados: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Error exportando resultados: {e}")
            return False
    
    def ejecutar_prediccion_completa(self, output_path, dias_futuros=28):
        """Ejecuta el pipeline completo de predicción"""
        
        print("🚀 EJECUTANDO PIPELINE COMPLETO DE PREDICCIÓN")
        print("=" * 60)
        
        # 1. Cargar modelo
        if not self.cargar_modelo():
            return False
        
        # 2. Generar predicciones
        predicciones = self.generar_predicciones_automaticas(dias_futuros)
        if predicciones is None:
            return False
        
        # 3. Detectar alertas
        alertas = self.detectar_alertas(predicciones)
        
        # 4. Generar recomendaciones
        recomendaciones = self.generar_recomendaciones_staffing(predicciones)
        
        # 5. Exportar resultados
        success = self.exportar_resultados(output_path, 'json')
        if success:
            self.exportar_resultados(output_path, 'excel')
        
        # 6. Mostrar resumen
        print(f"\n📊 RESUMEN DE PREDICCIÓN:")
        print(f"   📅 Período: {predicciones['ds'].min().date()} a {predicciones['ds'].max().date()}")
        print(f"   🎯 Promedio diario: {predicciones['yhat'].mean():.1f} horas-persona")
        print(f"   📈 Día pico: {predicciones.loc[predicciones['yhat'].idxmax(), 'ds'].strftime('%A %d/%m')} ({predicciones['yhat'].max():.1f}h)")
        print(f"   🚨 Alertas: {len(alertas)} detectadas")
        print(f"   💡 Recomendaciones: {len(recomendaciones)} generadas")
        
        return True

def main():
    """Función principal para generar predicciones"""
    
    print("🔮 INICIANDO GENERACIÓN DE PREDICCIONES CEAPSI")
    print("=" * 60)
    
    # Rutas
    # base_path = r"C:\Users\edgar\OneDrive\Documentos\BBDD CEAPSI\claude\analisis_resultados\forecasting"
    # modelo_path = f"{base_path}/modelo_prophet.pkl"
    # metadatos_path = f"{base_path}/metadatos_modelo.json"
    
    # Crear motor de predicción
    engine = CeapsiPredictionEngine(modelo_path, metadatos_path)
    
    # Ejecutar pipeline completo
    exito = engine.ejecutar_prediccion_completa(ruta_ultima, dias_futuros=28)
    
    if exito:
        print("\n🎉 PREDICCIONES GENERADAS EXITOSAMENTE")
        print(f"   📁 Resultados disponibles en: {ruta_ultima}")
    else:
        print("\n❌ Error en generación de predicciones")

if __name__ == "__main__":
    main()

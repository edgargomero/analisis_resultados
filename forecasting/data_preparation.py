#!/usr/bin/env python3
"""
CEAPSI Forecasting - Preparación de Datos para Prophet
Convierte datos normalizados a formato Prophet con regresores
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
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

# Ruta al archivo datos_normalizados.json más reciente
datos_input = os.path.join(ruta_ultima, "datos_normalizados.json")
print(f"📂 Usando datos normalizados de: {datos_input}")

# NUEVO: Definir output_path igual a la carpeta de entrada
output_path = ruta_ultima


class DataPreparationProphet:
    """Clase para preparar datos CEAPSI para modelo Prophet"""
    
    def __init__(self, datos_normalizados_path):
        self.datos_path = datos_normalizados_path
        self.df_prophet = None
        self.regresores = []
        
    def cargar_datos_normalizados(self):
        """Carga datos normalizados desde JSON"""
        try:
            with open(self.datos_path, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            
            print(f"✅ Datos cargados: {len(datos['reservas'])} reservas, "
                  f"{len(datos['conversaciones'])} conversaciones, "
                  f"{len(datos['llamadas'])} llamadas")
            
            return datos
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return None
    
    def consolidar_datos_diarios(self, datos_normalizados):
        """Consolida todas las transacciones en un único DataFrame."""
        
        lista_transacciones = []
        
        # Procesar Reservas
        for res in datos_normalizados.get('reservas', []):
            lista_transacciones.append({
                'fecha_str': res.get('fecha_str'),
                'fecha': pd.to_datetime(res.get('fecha')),
                'duracion': res.get('duracion', 45),
                'tipo': 'reserva',
                'especialidad': res.get('especialidad', ''),
                'cargo': res.get('cargo', 'NO_ESPECIFICADO'),         # <--- NUEVO
                'usuario': res.get('usuario', 'NO_ESPECIFICADO')      # <--- NUEVO
            })
            
        # Procesar Conversaciones
        for conv in datos_normalizados.get('conversaciones', []):
            lista_transacciones.append({
                'fecha_str': conv.get('fecha_str'),
                'fecha': pd.to_datetime(conv.get('fecha')),
                'duracion': conv.get('duracion', 10),
                'tipo': 'conversacion',
                'especialidad': '',
                'cargo': conv.get('cargo', 'NO_ESPECIFICADO'),        # <--- NUEVO
                'usuario': conv.get('usuario', 'NO_ESPECIFICADO')     # <--- NUEVO
            })
            
        # Procesar Llamadas
        for llamada in datos_normalizados.get('llamadas', []):
            lista_transacciones.append({
                'fecha_str': llamada.get('fecha_str'),
                'fecha': pd.to_datetime(llamada.get('fecha')),
                'duracion': llamada.get('duracion', 5),
                'tipo': 'llamada',
                'especialidad': '',
                'cargo': llamada.get('cargo', 'NO_ESPECIFICADO'),     # <--- NUEVO
                'usuario': llamada.get('usuario', 'NO_ESPECIFICADO')  # <--- NUEVO
            })
        
        if not lista_transacciones:
            print("⚠️ No se encontraron transacciones para consolidar.")
            # Devuelve un DataFrame vacío con las columnas esperadas para evitar errores posteriores
            return pd.DataFrame(columns=['fecha_str', 'fecha', 'duracion', 'tipo', 'especialidad'])

        df_transacciones = pd.DataFrame(lista_transacciones)
        print(f"📊 Total transacciones procesadas: {len(df_transacciones)}")
        
        # Agrupamiento por día, cargo y usuario
        if 'cargo' in df_transacciones.columns and 'usuario' in df_transacciones.columns:
            actividades_por_cargo_usuario = (
                df_transacciones
                .groupby(['fecha_str', 'cargo', 'usuario'])
                .size()
                .reset_index(name='actividades')
            )
            print("\nResumen de actividades por día, cargo y usuario (primeras filas):")
            print(actividades_por_cargo_usuario.head())
            actividades_por_cargo_usuario.to_csv('actividades_por_cargo_usuario.csv', index=False, encoding='utf-8-sig')
        else:
            print("⚠️ No se encontraron columnas 'cargo' y 'usuario' en las transacciones.")

        return df_transacciones
    def calcular_variable_objetivo(self, df_transacciones):
        """Calcula la carga de trabajo diaria en 'días-persona' (variable objetivo 'y')"""
        
        # Agrupar transacciones por día para sumar duraciones y contar eventos
        df_diario = df_transacciones.groupby('fecha_str').agg(
            duracion=('duracion', 'sum'),
            tipo=('tipo', 'count')
        ).reset_index()
        
        # Renombrar 'fecha_str' a 'ds' para compatibilidad con Prophet
        df_diario = df_diario.rename(columns={'fecha_str': 'ds'})
        df_diario['ds'] = pd.to_datetime(df_diario['ds'])
        
        # Calcular el total de horas de trabajo del día
        horas_totales = (
            df_diario['duracion'] / 60 +  # Convertir la suma de minutos a horas
            df_diario['tipo'] * 0.1       # Añadir 6 min (0.1h) de overhead por cada transacción
        )

        # --- INICIO DE LA CORRECCIÓN ---
        # Convertir las horas totales a "días-persona" (jornada de 8 horas).
        # Esta es una métrica mucho más estable y útil para el forecasting.
        df_diario['y'] = horas_totales / 8
        # --- FIN DE LA CORRECCIÓN ---

        df_objetivo = df_diario[['ds', 'y']]
        
        print(f"📈 Variable objetivo calculada. Promedio: {df_objetivo['y'].mean():.1f} días-persona/día")
        return df_objetivo
    
    def calcular_regresores(self, df_transacciones):
        """Calcula variables regresoras para el modelo Prophet."""
        
        # Se define el DataFrame como df_regresores
        df_regresores = df_transacciones.groupby('fecha_str').agg(
            volumen_reservas=('tipo', lambda x: (x == 'reserva').sum()),
            volumen_conversaciones=('tipo', lambda x: (x == 'conversacion').sum()),
            volumen_llamadas=('tipo', lambda x: (x == 'llamada').sum())
        ).reset_index()
        
        df_regresores = df_regresores.rename(columns={'fecha_str': 'ds'})
        df_regresores['ds'] = pd.to_datetime(df_regresores['ds'])
        
        # Regresores basados en fecha
        df_regresores['dia_semana'] = df_regresores['ds'].dt.dayofweek + 1
        df_regresores['es_inicio_mes'] = (df_regresores['ds'].dt.day <= 5).astype(int)
        
        # Regresor de profesionales disponibles
        df_regresores['profesionales_disponibles'] = np.maximum(5, np.ceil(df_regresores['volumen_reservas'] / 8))
        
        # Regresores de porcentaje por especialidad
        df_reservas = df_transacciones[df_transacciones['tipo'] == 'reserva']
        if 'especialidad' in df_reservas.columns:
            especialidades = df_reservas.pivot_table(index='fecha_str', columns='especialidad', aggfunc='size', fill_value=0)
            if len(especialidades.columns) > 0:
                total_reservas_dia = especialidades.sum(axis=1)
                for especialidad in especialidades.columns:
                    
                    if not (isinstance(especialidad, str) and especialidad.strip()):
                        continue

                    pct_col = f'pct_{especialidad.lower().replace(" ", "_")}'
                    porcentajes = (especialidades[especialidad] / total_reservas_dia.replace(0, 1)).fillna(0)
                    porcentajes_df = pd.DataFrame({'ds': porcentajes.index, pct_col: porcentajes.values})
                    porcentajes_df['ds'] = pd.to_datetime(porcentajes_df['ds'])

                    # --- INICIO DE LA CORRECCIÓN ---
                    # Se usa el nombre de variable consistente: df_regresores
                    df_regresores = pd.merge(df_regresores, porcentajes_df, on='ds', how='left')
                    df_regresores[pct_col] = df_regresores[pct_col].fillna(0)
                    # --- FIN DE LA CORRECCIÓN ---

        # --- INICIO DE LA CORRECCIÓN ---
        # Se usa el nombre de variable consistente: df_regresores
        self.regresores = [col for col in df_regresores.columns if col not in ['ds']]
        # --- FIN DE LA CORRECCIÓN ---
        print(f"🔧 Regresores calculados: {len(self.regresores)} variables")
        print(f"Variables: {self.regresores}")

        return df_regresores

    
    
        
        df_regresores = df_transacciones.groupby('fecha_str').agg(
            volumen_reservas=('tipo', lambda x: (x == 'reserva').sum()),
            volumen_conversaciones=('tipo', lambda x: (x == 'conversacion').sum()),
            volumen_llamadas=('tipo', lambda x: (x == 'llamada').sum())
        ).reset_index()
        
        df_regresores = df_regresores.rename(columns={'fecha_str': 'ds'})
        df_regresores['ds'] = pd.to_datetime(df_regresores['ds'])
        
        # Regresores basados en fecha
        df_regresores['dia_semana'] = df_regresores['ds'].dt.dayofweek + 1
        df_regresores['es_inicio_mes'] = (df_regresores['ds'].dt.day <= 5).astype(int)
        
        # Regresor de profesionales disponibles (basado en el volumen de reservas)
        df_regresores['profesionales_disponibles'] = np.maximum(5, np.ceil(df_regresores['volumen_reservas'] / 8))
        
        # Regresores de porcentaje por especialidad
        df_reservas = df_transacciones[df_transacciones['tipo'] == 'reserva']
        if 'especialidad' in df_reservas.columns:
            especialidades = df_reservas.pivot_table(index='fecha_str', columns='especialidad', aggfunc='size', fill_value=0)
            if len(especialidades.columns) > 0:
                total_reservas_dia = especialidades.sum(axis=1)
                for especialidad in especialidades.columns:
                    
                    # Asegurarse de que el nombre de la especialidad sea un string válido y no vacío
                    if not (isinstance(especialidad, str) and especialidad.strip()):
                        continue  # Saltar a la siguiente iteración si no es un nombre válido

                    pct_col = f'pct_{especialidad.lower().replace(" ", "_")}'
                    porcentajes = (especialidades[especialidad] / total_reservas_dia.replace(0, 1)).fillna(0)
                    porcentajes_df = pd.DataFrame({'ds': porcentajes.index, pct_col: porcentajes.values})
                    porcentajes_df['ds'] = pd.to_datetime(porcentajes_df['ds'])
                    regresores_df = pd.merge(regresores_df, porcentajes_df, on='ds', how='left')
                    regresores_df[pct_col] = regresores_df[pct_col].fillna(0)

        # Crear lista final de nombres de regresores
        self.regresores = [col for col in regresores_df.columns if col not in ['ds']]
        print(f"🔧 Regresores calculados: {len(self.regresores)} variables")
        print(f"Variables: {self.regresores}")

        return regresores_df
    
    def crear_dataframe_prophet(self):
        """Crea DataFrame final compatible con Prophet"""
        
        # 1. Cargar datos
        datos_normalizados = self.cargar_datos_normalizados()
        if not datos_normalizados:
            return None
        
        # 2. Consolidar transacciones
        df_transacciones = self.consolidar_datos_diarios(datos_normalizados)
        
        # 3. Calcular variable objetivo
        df_objetivo = self.calcular_variable_objetivo(df_transacciones)
        
        # Filtrar domingos (0=lunes, 6=domingo)
        df_objetivo = df_objetivo[df_objetivo['ds'].dt.dayofweek < 6]

        # Filtrar valores extremos
        df_objetivo = df_objetivo[(df_objetivo['y'] >= 10) & (df_objetivo['y'] <= 300)]

        # (Opcional) Eliminar outliers con IQR
        Q1 = df_objetivo['y'].quantile(0.25)
        Q3 = df_objetivo['y'].quantile(0.75)
        IQR = Q3 - Q1
        filtro = (df_objetivo['y'] >= Q1 - 1.5 * IQR) & (df_objetivo['y'] <= Q3 + 1.5 * IQR)
        df_objetivo = df_objetivo[filtro]
        
        # 4. Calcular regresores
        df_regresores = self.calcular_regresores(df_transacciones)
        
        # 5. Combinar objetivo y regresores
        self.df_prophet = pd.merge(df_objetivo[['ds', 'y']], df_regresores, on='ds', how='inner')
        
        # 6. Filtrar solo días laborales (lunes a sábado)
        self.df_prophet = self.df_prophet[self.df_prophet['ds'].dt.dayofweek < 6]
        
        # 7. Ordenar por fecha
        self.df_prophet = self.df_prophet.sort_values('ds').reset_index(drop=True)
        
        # 8. Guardar lista de regresores
        self.regresores = [col for col in self.df_prophet.columns if col not in ['ds', 'y']]
        
        print(f"\n✅ DataFrame Prophet creado:")
        print(f"   📅 Período: {self.df_prophet['ds'].min()} a {self.df_prophet['ds'].max()}")
        print(f"   📊 Total días: {len(self.df_prophet)}")
        print(f"   🎯 Variable objetivo promedio: {self.df_prophet['y'].mean():.1f} horas/día")
        print(f"   🔧 Regresores: {len(self.regresores)}")
        
        return self.df_prophet
    
    def validar_datos_prophet(self, return_messages=False):
        """Valida la calidad de los datos para Prophet"""
        
        if self.df_prophet is None:
            print("❌ No hay datos para validar")
            if return_messages:
                return False, ["❌ No hay datos para validar"]
            return False
        
        validaciones = []
        
        # 1. Verificar fechas continuas
        fechas_esperadas = pd.date_range(
            start=self.df_prophet['ds'].min(),
            end=self.df_prophet['ds'].max(),
            freq='D'
        )
        fechas_laborales = fechas_esperadas[fechas_esperadas.dayofweek < 6]
        
        if len(self.df_prophet) == len(fechas_laborales):
            validaciones.append("✅ Fechas continuas")
        else:
            validaciones.append(f"⚠️ Faltan {len(fechas_laborales) - len(self.df_prophet)} días")
        
        # 2. Verificar valores nulos
        nulos = self.df_prophet.isnull().sum().sum()
        if nulos == 0:
            validaciones.append("✅ Sin valores nulos")
        else:
            validaciones.append(f"⚠️ {nulos} valores nulos")
        
        # 3. Verificar rango de variable objetivo
        y_min, y_max = self.df_prophet['y'].min(), self.df_prophet['y'].max()
        if 10 <= y_min and y_max <= 100:
            validaciones.append("✅ Rango variable objetivo válido")
        else:
            validaciones.append(f"⚠️ Variable objetivo fuera de rango: {y_min:.1f} - {y_max:.1f}")
        
        # 4. Verificar variabilidad
        variabilidad = self.df_prophet['y'].std() / self.df_prophet['y'].mean()
        if 0.1 <= variabilidad <= 0.5:
            validaciones.append("✅ Variabilidad adecuada")
        else:
            validaciones.append(f"⚠️ Variabilidad: {variabilidad:.2f}")
        
        print("\n🔍 VALIDACIÓN DE DATOS:")
        for validacion in validaciones:
            print(f"   {validacion}")
        
        if return_messages:
            return all("✅" in v for v in validaciones), validaciones
        else:
            return all("✅" in v for v in validaciones)
    
    def guardar_datos_prophet(self, output_path, validacion=True, mensajes_validacion=None):
        """Guarda DataFrame Prophet y metadatos"""
        
        if self.df_prophet is None:
            print("❌ No hay datos para guardar")
            return False
        
        try:
            # Guardar DataFrame principal
            self.df_prophet.to_csv(f"{output_path}/datos_prophet.csv", index=False)
            
            # Guardar metadatos
            metadatos = {
                'fecha_generacion': datetime.now().isoformat(),
                'periodo_datos': {
                    'inicio': self.df_prophet['ds'].min().isoformat(),
                    'fin': self.df_prophet['ds'].max().isoformat(),
                    'total_dias': len(self.df_prophet)
                },
                'variable_objetivo': {
                    'nombre': 'horas_persona_necesarias',
                    'promedio': float(self.df_prophet['y'].mean()),
                    'desviacion': float(self.df_prophet['y'].std()),
                    'minimo': float(self.df_prophet['y'].min()),
                    'maximo': float(self.df_prophet['y'].max())
                },
                'regresores': self.regresores,
                'estadisticas_regresores': {},
                'validacion_exitosa': validacion,
                'mensajes_validacion': mensajes_validacion or []
            }
            
            # Estadísticas de regresores
            for regresor in self.regresores:
                metadatos['estadisticas_regresores'][regresor] = {
                    'promedio': float(self.df_prophet[regresor].mean()),
                    'desviacion': float(self.df_prophet[regresor].std()),
                    'minimo': float(self.df_prophet[regresor].min()),
                    'maximo': float(self.df_prophet[regresor].max())
                }
            
            with open(f"{output_path}/metadatos_prophet.json", 'w', encoding='utf-8') as f:
                json.dump(metadatos, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Datos Prophet guardados en {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error guardando datos: {e}")
            return False
    
    def generar_resumen_estadistico(self):
        """Genera resumen estadístico de los datos preparados"""
        
        if self.df_prophet is None:
            print("❌ No hay datos para analizar")
            return None
        
        print("\n📊 RESUMEN ESTADÍSTICO - DATOS PROPHET")
        print("=" * 50)
        
        # Variable objetivo
        print(f"\n🎯 VARIABLE OBJETIVO (y = horas_persona_necesarias):")
        print(f"   Promedio: {self.df_prophet['y'].mean():.1f} horas/día")
        print(f"   Mediana: {self.df_prophet['y'].median():.1f} horas/día")
        print(f"   Desv. Estándar: {self.df_prophet['y'].std():.1f} horas")
        print(f"   Rango: {self.df_prophet['y'].min():.1f} - {self.df_prophet['y'].max():.1f} horas")
        
        # Regresores principales
        print(f"\n🔧 REGRESORES PRINCIPALES:")
        for regresor in ['volumen_reservas', 'volumen_conversaciones', 'volumen_llamadas']:
            if regresor in self.df_prophet.columns:
                valores = self.df_prophet[regresor]
                print(f"   {regresor}: μ={valores.mean():.1f}, σ={valores.std():.1f}, rango=[{valores.min()}-{valores.max()}]")
        
        # Correlaciones con variable objetivo
        print(f"\n📈 CORRELACIONES CON VARIABLE OBJETIVO:")
        for regresor in self.regresores:
            if self.df_prophet[regresor].dtype in ['int64', 'float64']:
                corr = self.df_prophet['y'].corr(self.df_prophet[regresor])
                print(f"   {regresor}: {corr:.3f}")
        
        # Tendencia temporal
        self.df_prophet['semana'] = self.df_prophet['ds'].dt.isocalendar().week
        tendencia_semanal = self.df_prophet.groupby('semana')['y'].mean()
        
        print(f"\n📅 TENDENCIA SEMANAL:")
        print(f"   Semana con mayor demanda: Semana {tendencia_semanal.idxmax()} ({tendencia_semanal.max():.1f}h)")
        print(f"   Semana con menor demanda: Semana {tendencia_semanal.idxmin()} ({tendencia_semanal.min():.1f}h)")
        
        return {
            'variable_objetivo': self.df_prophet['y'].describe().to_dict(),
            'correlaciones': {reg: self.df_prophet['y'].corr(self.df_prophet[reg]) 
                            for reg in self.regresores if self.df_prophet[reg].dtype in ['int64', 'float64']},
            'tendencia_semanal': tendencia_semanal.to_dict()
        }

def main():
    """Función principal de preparación de datos"""
    
    print("🚀 INICIANDO PREPARACIÓN DE DATOS PARA PROPHET")
    print("=" * 60)
    
    # Rutas
    # output_path = r"C:\Users\edgar\OneDrive\Documentos\BBDD CEAPSI\claude\analisis_resultados\forecasting"
    
    # Crear preparador
    preparador = DataPreparationProphet(datos_input)
    
    # Crear DataFrame Prophet
    df_prophet = preparador.crear_dataframe_prophet()
    
    if df_prophet is not None:
        # Validar datos
        es_valido, mensajes_validacion = preparador.validar_datos_prophet(return_messages=True)
        
        # Generar resumen
        resumen = preparador.generar_resumen_estadistico()
        
        # Guardar resultados SIEMPRE, incluyendo el estado de validación
        exito = preparador.guardar_datos_prophet(output_path, validacion=es_valido, mensajes_validacion=mensajes_validacion)
        if exito:
            print("\n🎉 PREPARACIÓN DE DATOS COMPLETADA EXITOSAMENTE")
            if not es_valido:
                print("⚠️ Advertencia: Los datos NO pasaron la validación. Revisa los reportes y resultados para más detalles.")
        else:
            print("\n❌ Error guardando datos preparados")
    else:
        print("\n❌ Error en preparación de datos")

if __name__ == "__main__":
    main()

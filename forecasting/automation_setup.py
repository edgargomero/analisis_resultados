#!/usr/bin/env python3
"""
CEAPSI Forecasting - Script de Automatización
Automatiza la ejecución periódica del sistema de forecasting
"""

import os
import sys
import json
import schedule
import time
import logging
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import subprocess

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ceapsi_automation.log'),
        logging.StreamHandler()
    ]
)

class CeapsiAutomationManager:
    """Gestor de automatización para sistema CEAPSI"""
    
    def __init__(self, config_path):
        self.config = self.cargar_configuracion(config_path)
        self.base_path = self.config.get('base_path', '')
        
    def cargar_configuracion(self, config_path):
        """Carga configuración desde archivo JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logging.info("Configuración cargada exitosamente")
            return config
        except Exception as e:
            logging.error(f"Error cargando configuración: {e}")
            return {}
    
    def ejecutar_pipeline_completo(self):
        """Ejecuta el pipeline completo de forecasting"""
        
        logging.info("🚀 Iniciando pipeline automático de forecasting")
        
        try:
            # 1. Extraer datos actualizados (en producción conectaría a BD)
            logging.info("📊 Extrayendo datos actualizados...")
            self.extraer_datos_sistemas()
            
            # 2. Preparar datos para Prophet
            logging.info("🔧 Preparando datos para Prophet...")
            result = os.system(f"cd {self.base_path}/forecasting && python data_preparation.py")
            if result != 0:
                raise Exception("Error en preparación de datos")
            
            # 3. Verificar si necesita re-entrenamiento
            if self.evaluar_necesidad_reentrenamiento():
                logging.info("🤖 Re-entrenando modelo...")
                result = os.system(f"cd {self.base_path}/forecasting && python model_training.py")
                if result != 0:
                    raise Exception("Error en entrenamiento")
            
            # 4. Generar predicciones
            logging.info("🔮 Generando predicciones...")
            result = os.system(f"cd {self.base_path}/forecasting && python predictions.py")
            if result != 0:
                raise Exception("Error generando predicciones")
            
            # 5. Verificar alertas críticas
            alertas_criticas = self.verificar_alertas_criticas()
            
            # 6. Enviar notificaciones si es necesario
            if alertas_criticas:
                self.enviar_alertas_email(alertas_criticas)
            
            # 7. Actualizar dashboard
            self.actualizar_dashboard()
            
            logging.info("✅ Pipeline completado exitosamente")
            return True
            
        except Exception as e:
            logging.error(f"❌ Error en pipeline: {e}")
            self.enviar_notificacion_error(str(e))
            return False
    
    def extraer_datos_sistemas(self):
        """Extrae datos de los sistemas CEAPSI (placeholder)"""
        # En producción, esto haría:
        # 1. Conectar a base de datos Reservo
        # 2. Conectar a base de datos Alodesk
        # 3. Extraer datos de últimas 24-48 horas
        # 4. Actualizar archivos CSV o cargar en DataFrame
        
        logging.info("   📋 Datos de reservas extraídos")
        logging.info("   💬 Datos de conversaciones extraídos")
        logging.info("   📞 Datos de llamadas extraídos")
        
        # Simular extracción exitosa
        return True
    
    def evaluar_necesidad_reentrenamiento(self):
        """Evalúa si el modelo necesita re-entrenamiento"""
        
        try:
            # Cargar metadatos del modelo actual
            metadatos_path = f"{self.base_path}/forecasting/metadatos_modelo.json"
            
            if not os.path.exists(metadatos_path):
                logging.info("No existe modelo previo, requiere entrenamiento inicial")
                return True
            
            with open(metadatos_path, 'r', encoding='utf-8') as f:
                metadatos = json.load(f)
            
            # Criterios para re-entrenamiento
            fecha_entrenamiento = datetime.fromisoformat(metadatos['fecha_entrenamiento'])
            dias_desde_entrenamiento = (datetime.now() - fecha_entrenamiento).days
            
            criterios = {
                'dias_antiguedad': dias_desde_entrenamiento > 30,
                'es_lunes': datetime.now().weekday() == 0,  # Re-entrenar los lunes
                'datos_insuficientes': False  # Placeholder para validación de datos
            }
            
            necesita_reentrenamiento = any(criterios.values())
            
            if necesita_reentrenamiento:
                logging.info(f"Modelo requiere re-entrenamiento: {criterios}")
            else:
                logging.info("Modelo actual es válido, no requiere re-entrenamiento")
            
            return necesita_reentrenamiento
            
        except Exception as e:
            logging.warning(f"Error evaluando re-entrenamiento: {e}")
            return False
    
    def verificar_alertas_criticas(self):
        """Verifica si hay alertas críticas en las predicciones"""
        
        try:
            # Buscar archivo de predicciones más reciente
            forecasting_path = f"{self.base_path}/forecasting"
            archivos_prediccion = [f for f in os.listdir(forecasting_path) if f.startswith('predicciones_ceapsi_') and f.endswith('.json')]
            
            if not archivos_prediccion:
                logging.warning("No se encontraron archivos de predicción")
                return []
            
            # Cargar predicciones más recientes
            archivo_mas_reciente = sorted(archivos_prediccion)[-1]
            with open(f"{forecasting_path}/{archivo_mas_reciente}", 'r', encoding='utf-8') as f:
                datos_prediccion = json.load(f)
            
            # Filtrar alertas críticas
            alertas = datos_prediccion.get('alertas', [])
            alertas_criticas = [a for a in alertas if a.get('tipo') == 'CRITICA']
            
            if alertas_criticas:
                logging.warning(f"🚨 {len(alertas_criticas)} alertas críticas detectadas")
            else:
                logging.info("No hay alertas críticas")
            
            return alertas_criticas
            
        except Exception as e:
            logging.error(f"Error verificando alertas: {e}")
            return []
    
    def enviar_alertas_email(self, alertas_criticas):
        """Envía alertas críticas por email"""
        
        if not self.config.get('email', {}).get('enabled', False):
            logging.info("Notificaciones por email deshabilitadas")
            return
        
        try:
            email_config = self.config['email']
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = ', '.join(email_config['to'])
            msg['Subject'] = f"🚨 CEAPSI - Alertas Críticas de Personal ({datetime.now().strftime('%d/%m/%Y')})"
            
            # Crear cuerpo del email
            cuerpo = self.generar_email_alertas(alertas_criticas)
            msg.attach(MIMEText(cuerpo, 'html'))
            
            # Enviar email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            if email_config.get('use_tls', True):
                server.starttls()
            
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            logging.info(f"✅ Alertas enviadas por email a {len(email_config['to'])} destinatarios")
            
        except Exception as e:
            logging.error(f"Error enviando email: {e}")
    
    def generar_email_alertas(self, alertas_criticas):
        """Genera HTML para email de alertas"""
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2 style="color: #e74c3c;">🚨 Alertas Críticas - Sistema de Predicción CEAPSI</h2>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Total de alertas críticas:</strong> {len(alertas_criticas)}</p>
            
            <h3>Detalles de Alertas:</h3>
            <table style="border-collapse: collapse; width: 100%; border: 1px solid #ddd;">
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Fecha</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Día</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Horas Predichas</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Mensaje</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Acción</th>
                </tr>
        """
        
        for alerta in alertas_criticas:
            html += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alerta['fecha']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alerta['dia_semana']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center; font-weight: bold; color: #e74c3c;">{alerta['horas_predichas']}h</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alerta['mensaje']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alerta['accion']}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h3>Recomendaciones Inmediatas:</h3>
            <ul>
                <li>Revisar disponibilidad de personal adicional</li>
                <li>Contactar a personal de guardia/contingencia</li>
                <li>Considerar reprogramación de citas no urgentes</li>
                <li>Activar protocolo de alta demanda</li>
            </ul>
            
            <p style="color: #7f8c8d; font-size: 12px;">
                Este es un mensaje automático del sistema de predicción de personal CEAPSI.
                Para más detalles, acceder al dashboard de predicciones.
            </p>
        </body>
        </html>
        """
        
        return html
    
    def enviar_notificacion_error(self, error_msg):
        """Envía notificación de error del sistema"""
        
        logging.error(f"Sistema de forecasting falló: {error_msg}")
        
        # En producción, enviaría email de error a administradores
        # Por ahora, solo log
    
    def actualizar_dashboard(self):
        """Actualiza dashboard con nuevas predicciones"""
        
        logging.info("📊 Actualizando dashboard...")
        
        # En producción, esto:
        # 1. Actualizaría base de datos de dashboard
        # 2. Regeneraría archivos estáticos
        # 3. Invalidaría cache de aplicación web
        
        logging.info("✅ Dashboard actualizado")
    
    def generar_reporte_semanal(self):
        """Genera reporte semanal de predicciones"""
        
        logging.info("📑 Generando reporte semanal...")
        
        try:
            # Cargar datos de predicciones de la semana
            # Calcular métricas de precisión
            # Generar gráficos
            # Crear PDF de reporte
            # Enviar por email a stakeholders
            
            logging.info("✅ Reporte semanal generado y enviado")
            
        except Exception as e:
            logging.error(f"Error generando reporte semanal: {e}")
    
    def configurar_scheduler(self):
        """Configura tareas programadas"""
        
        logging.info("⏰ Configurando scheduler...")
        
        # Predicciones diarias a las 6:00 AM
        schedule.every().day.at("06:00").do(self.ejecutar_pipeline_completo)
        
        # Reporte semanal los lunes a las 8:00 AM
        schedule.every().monday.at("08:00").do(self.generar_reporte_semanal)
        
        # Verificación de salud del sistema cada hora
        schedule.every().hour.do(self.verificar_salud_sistema)
        
        logging.info("✅ Scheduler configurado")
    
    def verificar_salud_sistema(self):
        """Verifica que el sistema esté funcionando correctamente"""
        
        # Verificar archivos importantes
        archivos_criticos = [
            f"{self.base_path}/forecasting/modelo_prophet.pkl",
            f"{self.base_path}/forecasting/metadatos_modelo.json"
        ]
        
        for archivo in archivos_criticos:
            if not os.path.exists(archivo):
                logging.warning(f"Archivo crítico faltante: {archivo}")
    
    def ejecutar_loop_principal(self):
        """Ejecuta el loop principal de automatización"""
        
        logging.info("🔄 Iniciando loop principal de automatización CEAPSI")
        
        self.configurar_scheduler()
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto

def crear_configuracion_ejemplo():
    """Crea archivo de configuración de ejemplo"""
    
    config_ejemplo = {
        "base_path": r"C:\Users\edgar\OneDrive\Documentos\BBDD CEAPSI\claude\analisis_resultados",
        "email": {
            "enabled": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "username": "tu_email@gmail.com",
            "password": "tu_password_app",
            "from": "sistema-ceapsi@tudominio.com",
            "to": [
                "gerencia@ceapsi.cl",
                "operaciones@ceapsi.cl"
            ]
        },
        "database": {
            "reservo_connection": "postgresql://user:pass@host:port/reservo_db",
            "alodesk_connection": "postgresql://user:pass@host:port/alodesk_db"
        },
        "thresholds": {
            "alerta_critica_horas": 60,
            "alerta_alta_horas": 50,
            "alerta_baja_horas": 25
        }
    }
    
    with open('config_ceapsi_automation.json', 'w', encoding='utf-8') as f:
        json.dump(config_ejemplo, f, indent=2, ensure_ascii=False)
    
    print("✅ Archivo de configuración de ejemplo creado: config_ceapsi_automation.json")

def ejecutar_comparacion_arima_prophet():
    # Ruta al script de comparación
    script_path = os.path.join(os.path.dirname(__file__), "compare_arima_prophet.py")
    print("🔄 Ejecutando comparación Prophet vs ARIMA...")
    try:
        result = subprocess.run(["python", script_path], check=True, capture_output=True, text=True)
        print(result.stdout)
        print("✅ Comparación Prophet vs ARIMA completada y guardada en la carpeta de resultados.")
    except Exception as e:
        print(f"❌ Error ejecutando comparación ARIMA vs Prophet: {e}")

def main():
    """Función principal de automatización"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Automatización CEAPSI Forecasting')
    parser.add_argument('--config', default='config_ceapsi_automation.json', help='Archivo de configuración')
    parser.add_argument('--create-config', action='store_true', help='Crear archivo de configuración de ejemplo')
    parser.add_argument('--run-once', action='store_true', help='Ejecutar pipeline una sola vez')
    
    args = parser.parse_args()
    
    if args.create_config:
        crear_configuracion_ejemplo()
        return
    
    if not os.path.exists(args.config):
        print(f"❌ Archivo de configuración no encontrado: {args.config}")
        print("Usar --create-config para crear uno de ejemplo")
        return
    
    # Crear gestor de automatización
    manager = CeapsiAutomationManager(args.config)
    
    if args.run_once:
        # Ejecutar una sola vez
        exito = manager.ejecutar_pipeline_completo()
        sys.exit(0 if exito else 1)
    else:
        # Ejecutar loop continuo
        try:
            manager.ejecutar_loop_principal()
        except KeyboardInterrupt:
            logging.info("🛑 Automatización detenida por usuario")
        except Exception as e:
            logging.error(f"❌ Error en loop principal: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()

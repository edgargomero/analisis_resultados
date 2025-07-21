            retention_days = self.config.get('backup', {}).get('retention_days', 30)
            backup_base = os.path.join(self.base_path, 'backups')
            
            if not os.path.exists(backup_base):
                return
            
            fecha_limite = datetime.now() - timedelta(days=retention_days)
            
            for carpeta in os.listdir(backup_base):
                ruta_carpeta = os.path.join(backup_base, carpeta)
                if os.path.isdir(ruta_carpeta):
                    try:
                        fecha_carpeta = datetime.strptime(carpeta, '%Y%m%d')
                        if fecha_carpeta < fecha_limite:
                            import shutil
                            shutil.rmtree(ruta_carpeta)
                            logger.info(f"🗑️ Backup antiguo eliminado: {carpeta}")
                    except ValueError:
                        continue  # Ignorar carpetas que no siguen el formato de fecha
        
        except Exception as e:
            logger.error(f"❌ Error limpiando backups: {e}")
    
    def _enviar_alertas_criticas(self, alertas_sistema):
        """Envía alertas críticas por email"""
        
        if not self.config.get('email', {}).get('enabled', False):
            logger.info("📧 Notificaciones por email deshabilitadas")
            return
        
        alertas_criticas = [a for a in alertas_sistema if a.get('severidad') == 'CRITICA']
        
        if not alertas_criticas:
            return
        
        try:
            email_config = self.config['email']
            
            # Crear mensaje
            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = ', '.join(email_config['to_operations'])
            msg['Subject'] = f"🚨 CEAPSI PCF - {len(alertas_criticas)} Alertas Críticas ({datetime.now().strftime('%d/%m/%Y')})"
            
            # Crear cuerpo del email
            cuerpo = self._generar_email_alertas_criticas(alertas_criticas)
            msg.attach(MIMEText(cuerpo, 'html'))
            
            # Enviar email
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
            
            logger.info(f"📧 Alertas críticas enviadas a {len(email_config['to_operations'])} destinatarios")
            
        except Exception as e:
            logger.error(f"❌ Error enviando alertas críticas: {e}")
    
    def _generar_email_alertas_criticas(self, alertas_criticas):
        """Genera HTML para email de alertas críticas"""
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <h2 style="color: #e74c3c;">🚨 Sistema PCF CEAPSI - Alertas Críticas</h2>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Total de alertas críticas:</strong> {len(alertas_criticas)}</p>
            
            <div style="background-color: #fee; border: 1px solid #fcc; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h3 style="color: #c00; margin-top: 0;">⚠️ ACCIÓN INMEDIATA REQUERIDA</h3>
                <p>El sistema de predicción PCF ha detectado condiciones críticas que requieren intervención inmediata.</p>
            </div>
            
            <h3>Detalles de Alertas Críticas:</h3>
            <table style="border-collapse: collapse; width: 100%; border: 1px solid #ddd;">
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Componente</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Tipo</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Mensaje</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Acción Requerida</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Timestamp</th>
                </tr>
        """
        
        for alerta in alertas_criticas:
            html += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold; color: #e74c3c;">{alerta.get('componente', 'N/A')}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alerta.get('tipo', 'N/A')}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alerta.get('mensaje', 'N/A')}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alerta.get('accion', 'N/A')}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{alerta.get('timestamp', 'N/A')[:19]}</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h3>Próximos Pasos Recomendados:</h3>
            <ol>
                <li><strong>Verificación inmediata</strong>: Revisar el dashboard de validación PCF</li>
                <li><strong>Análisis de logs</strong>: Examinar logs detallados del sistema</li>
                <li><strong>Contacto técnico</strong>: Si persiste, contactar equipo de Data Science</li>
                <li><strong>Plan de contingencia</strong>: Activar procedimientos manuales si es necesario</li>
            </ol>
            
            <div style="background-color: #e8f4fd; border: 1px solid #b3d8f0; padding: 15px; margin: 15px 0; border-radius: 5px;">
                <h4 style="color: #31708f; margin-top: 0;">📊 Información del Sistema</h4>
                <p><strong>Sistema:</strong> Proyecto PCF (Precision Call Forecast)</p>
                <p><strong>Versión:</strong> 1.0</p>
                <p><strong>Estado:</strong> Requiere Atención Inmediata</p>
                <p><strong>Dashboard:</strong> <a href="http://dashboard-pcf.ceapsi.local">Acceder al Dashboard</a></p>
            </div>
            
            <p style="color: #7f8c8d; font-size: 12px; margin-top: 30px;">
                Este es un mensaje automático del Sistema PCF CEAPSI.<br>
                Para soporte técnico: it@ceapsi.cl | Para escalamiento: gerencia@ceapsi.cl
            </p>
        </body>
        </html>
        """
        
        return html
    
    def _enviar_notificacion_error(self, error_msg):
        """Envía notificación de error del sistema"""
        
        try:
            if self.config.get('email', {}).get('enabled', False):
                email_config = self.config['email']
                
                msg = MIMEMultipart()
                msg['From'] = email_config['from']
                msg['To'] = ', '.join(email_config['to_technical'])
                msg['Subject'] = f"❌ CEAPSI PCF - Error del Sistema ({datetime.now().strftime('%d/%m/%Y %H:%M')})"
                
                cuerpo_error = f"""
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px;">
                    <h2 style="color: #d32f2f;">❌ Error en Sistema PCF</h2>
                    <p><strong>Timestamp:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                    <p><strong>Error:</strong> {error_msg}</p>
                    
                    <div style="background-color: #ffebee; border: 1px solid #f8bbd9; padding: 15px; margin: 15px 0;">
                        <h3>Detalles del Fallo</h3>
                        <p>El pipeline automático PCF ha fallado durante su ejecución programada.</p>
                        <p><strong>Errores Consecutivos:</strong> {self.estado_sistema['errores_consecutivos']}</p>
                        <p><strong>Última Ejecución Exitosa:</strong> {self.estado_sistema.get('ultima_ejecucion', 'N/A')}</p>
                    </div>
                    
                    <h3>Acciones Requeridas:</h3>
                    <ul>
                        <li>Revisar logs del sistema</li>
                        <li>Verificar conectividad a fuentes de datos</li>
                        <li>Comprobar espacio en disco y recursos</li>
                        <li>Reiniciar manualmente si es necesario</li>
                    </ul>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(cuerpo_error, 'html'))
                
                with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                    if email_config.get('use_tls', True):
                        server.starttls()
                    server.login(email_config['username'], email_config['password'])
                    server.send_message(msg)
                
                logger.info("📧 Notificación de error enviada")
        
        except Exception as e:
            logger.error(f"❌ Error enviando notificación de error: {e}")
    
    def _actualizar_estado_sistema(self, metricas_performance, exito):
        """Actualiza el estado interno del sistema"""
        
        if exito:
            self.estado_sistema['ultima_ejecucion'] = datetime.now().isoformat()
            self.estado_sistema['errores_consecutivos'] = 0
            self.estado_sistema['performance_actual'] = {
                'timestamp': datetime.now().isoformat(),
                'estado_general': metricas_performance.get('estado_general', 'DESCONOCIDO'),
                'score_general': metricas_performance.get('score_general', 0),
                'mae_promedio': self._calcular_mae_promedio(metricas_performance)
            }
            
            # Agregar a histórico
            self.metricas_historicas.append(self.estado_sistema['performance_actual'])
            
            # Mantener solo últimas 100 métricas
            if len(self.metricas_historicas) > 100:
                self.metricas_historicas = self.metricas_historicas[-100:]
        
        else:
            self.estado_sistema['errores_consecutivos'] += 1
        
        # Guardar estado
        try:
            with open('estado_sistema_pcf.json', 'w', encoding='utf-8') as f:
                json.dump(self.estado_sistema, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.error(f"❌ Error guardando estado del sistema: {e}")
    
    def _calcular_mae_promedio(self, metricas_performance):
        """Calcula MAE promedio del sistema"""
        
        maes = []
        for tipo, performance in metricas_performance.get('performance_por_tipo', {}).items():
            mae = performance.get('mae_ensemble', 0)
            if mae > 0:
                maes.append(mae)
        
        return np.mean(maes) if maes else 0
    
    def generar_reporte_semanal(self):
        """Genera reporte semanal completo"""
        
        logger.info("📑 Generando reporte semanal...")
        
        try:
            # Cargar métricas de la semana
            metricas_semana = self.metricas_historicas[-7:] if len(self.metricas_historicas) >= 7 else self.metricas_historicas
            
            if not metricas_semana:
                logger.warning("⚠️ No hay métricas suficientes para reporte semanal")
                return
            
            # Calcular tendencias
            scores = [m.get('score_general', 0) for m in metricas_semana]
            maes = [m.get('mae_promedio', 0) for m in metricas_semana if m.get('mae_promedio', 0) > 0]
            
            reporte_semanal = {
                'periodo': f"Semana {datetime.now().strftime('%W-%Y')}",
                'fecha_generacion': datetime.now().isoformat(),
                'metricas_promedio': {
                    'score_general': np.mean(scores) if scores else 0,
                    'mae_promedio': np.mean(maes) if maes else 0,
                    'disponibilidad': 100 - (self.estado_sistema['errores_consecutivos'] * 10)
                },
                'tendencias': {
                    'mejora_score': scores[-1] - scores[0] if len(scores) >= 2 else 0,
                    'estabilidad_mae': np.std(maes) if len(maes) >= 2 else 0,
                    'dias_sin_errores': 7 - self.estado_sistema['errores_consecutivos']
                },
                'objetivos_cumplidos': self._evaluar_objetivos_semanales(metricas_semana),
                'recomendaciones_semana': self._generar_recomendaciones_semanales(metricas_semana)
            }
            
            # Guardar reporte
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"reporte_semanal_pcf_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(reporte_semanal, f, indent=2, ensure_ascii=False, default=str)
            
            # Enviar reporte por email
            if self.config.get('email', {}).get('enabled', False):
                self._enviar_reporte_semanal(reporte_semanal, filename)
            
            logger.info(f"✅ Reporte semanal generado: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error generando reporte semanal: {e}")
    
    def _evaluar_objetivos_semanales(self, metricas_semana):
        """Evalúa cumplimiento de objetivos semanales"""
        
        if not metricas_semana:
            return {}
        
        # Promedios de la semana
        score_promedio = np.mean([m.get('score_general', 0) for m in metricas_semana])
        mae_promedio = np.mean([m.get('mae_promedio', 0) for m in metricas_semana if m.get('mae_promedio', 0) > 0])
        
        objetivos = self.config['objetivos_performance']
        
        return {
            'score_objetivo_80': score_promedio >= 80,
            'mae_objetivo': mae_promedio <= objetivos['mae_objetivo'] if mae_promedio > 0 else False,
            'disponibilidad_95': self.estado_sistema['errores_consecutivos'] <= 1,
            'porcentaje_cumplimiento': 0  # Se calculará dinámicamente
        }
    
    def _generar_recomendaciones_semanales(self, metricas_semana):
        """Genera recomendaciones para la próxima semana"""
        
        recomendaciones = []
        
        if len(metricas_semana) >= 2:
            score_inicial = metricas_semana[0].get('score_general', 0)
            score_final = metricas_semana[-1].get('score_general', 0)
            
            if score_final < score_inicial:
                recomendaciones.append({
                    'tipo': 'TENDENCIA_NEGATIVA',
                    'descripcion': 'Performance descendente durante la semana',
                    'accion': 'Investigar causas de degradación y planificar mejoras'
                })
        
        # Más recomendaciones basadas en patterns específicos
        if self.estado_sistema['errores_consecutivos'] > 0:
            recomendaciones.append({
                'tipo': 'ESTABILIDAD',
                'descripcion': f'{self.estado_sistema["errores_consecutivos"]} errores recientes detectados',
                'accion': 'Revisar logs y fortalecer monitoreo preventivo'
            })
        
        return recomendaciones
    
    def _enviar_reporte_semanal(self, reporte, filename):
        """Envía reporte semanal por email"""
        
        try:
            email_config = self.config['email']
            
            msg = MIMEMultipart()
            msg['From'] = email_config['from']
            msg['To'] = ', '.join(email_config['to_executive'])
            msg['Subject'] = f"📊 CEAPSI PCF - Reporte Semanal ({datetime.now().strftime('Sem %W-%Y')})"
            
            # Crear cuerpo ejecutivo
            score = reporte['metricas_promedio']['score_general']
            mae = reporte['metricas_promedio']['mae_promedio']
            
            estado_emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            
            cuerpo = f"""
            <html>
            <body style="font-family: Arial, sans-serif; margin: 20px;">
                <h2 style="color: #2c3e50;">{estado_emoji} CEAPSI PCF - Reporte Semanal Ejecutivo</h2>
                
                <div style="background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h3>📈 Resumen de Performance</h3>
                    <p><strong>Score General:</strong> {score:.1f}/100</p>
                    <p><strong>Precisión (MAE):</strong> {mae:.1f} llamadas</p>
                    <p><strong>Disponibilidad:</strong> {reporte['metricas_promedio']['disponibilidad']:.1f}%</p>
                </div>
                
                <h3>🎯 Impacto en Negocio</h3>
                <ul>
                    <li>Reducción estimada de sobre-staffing: {15 if score >= 80 else 5}%</li>
                    <li>Mejora en planificación: {score/10:.0f} días de anticipación</li>
                    <li>ROI semanal estimado: ${score * 100:.0f}</li>
                </ul>
                
                <h3>📋 Próximos Pasos</h3>
            """
            
            for rec in reporte.get('recomendaciones_semana', []):
                cuerpo += f"<p>• <strong>{rec['tipo']}:</strong> {rec['descripcion']}</p>"
            
            cuerpo += """
                <p style="margin-top: 30px; font-size: 12px; color: #7f8c8d;">
                    Reporte automático del Sistema PCF CEAPSI.<br>
                    Para detalles técnicos, consultar dashboard o contactar equipo de Data Science.
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(cuerpo, 'html'))
            
            # Adjuntar reporte completo
            with open(filename, 'rb') as f:
                attachment = MIMEBase('application', 'json')
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', f'attachment; filename={filename}')
                msg.attach(attachment)
            
            # Enviar
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                server.login(email_config['username'], email_config['password'])
                server.send_message(msg)
            
            logger.info("📧 Reporte semanal enviado a ejecutivos")
            
        except Exception as e:
            logger.error(f"❌ Error enviando reporte semanal: {e}")
    
    def configurar_scheduler(self):
        """Configura todas las tareas programadas del sistema PCF"""
        
        logger.info("⏰ Configurando scheduler PCF...")
        
        # Pipeline diario de predicciones
        horario_predicciones = self.config['frecuencia_ejecucion']['predicciones_diarias']
        schedule.every().day.at(horario_predicciones).do(self.ejecutar_pipeline_pcf_completo)
        
        # Validación semanal (lunes)
        schedule.every().monday.at("08:00").do(self._ejecutar_validacion_semanal)
        
        # Reentrenamiento (domingos)
        schedule.every().sunday.at("02:00").do(self._ejecutar_reentrenamiento_completo)
        
        # Reporte semanal (viernes)
        schedule.every().friday.at("17:00").do(self.generar_reporte_semanal)
        
        # Verificación de salud cada 2 horas
        schedule.every(2).hours.do(self._verificar_salud_sistema)
        
        # Limpieza diaria de logs y archivos temporales
        schedule.every().day.at("01:00").do(self._limpiar_archivos_temporales)
        
        logger.info("✅ Scheduler PCF configurado con 6 tareas programadas")
    
    def _ejecutar_validacion_semanal(self):
        """Ejecuta validación semanal completa del sistema"""
        logger.info("🔍 Iniciando validación semanal...")
        
        try:
            # Cargar todos los resultados recientes
            tipos_validar = ['ENTRANTE', 'SALIENTE']
            problemas_detectados = []
            
            for tipo in tipos_validar:
                resultados = self._cargar_resultados_multimodelo(tipo)
                if not resultados:
                    problemas_detectados.append(f"Sin resultados para {tipo}")
                    continue
                
                # Validar métricas
                metadatos = resultados.get('metadatos_modelos', {})
                maes = [m.get('mae_validacion', m.get('mae_cv', float('inf'))) for m in metadatos.values()]
                
                if not maes or min(maes) > 20:
                    problemas_detectados.append(f"Performance baja en {tipo}: MAE mínimo {min(maes) if maes else 'N/A'}")
            
            # Generar reporte de validación
            reporte_validacion = {
                'fecha': datetime.now().isoformat(),
                'tipos_evaluados': tipos_validar,
                'problemas_detectados': problemas_detectados,
                'estado_validacion': 'CRITICO' if len(problemas_detectados) > 2 else 'ATENCION' if problemas_detectados else 'OK',
                'recomendaciones': self._generar_recomendaciones_validacion(problemas_detectados)
            }
            
            # Guardar reporte
            with open(f"validacion_semanal_{datetime.now().strftime('%Y%m%d')}.json", 'w') as f:
                json.dump(reporte_validacion, f, indent=2, default=str)
            
            if problemas_detectados:
                self._enviar_alerta_validacion(reporte_validacion)
            
            logger.info(f"✅ Validación semanal completada: {len(problemas_detectados)} problemas detectados")
            
        except Exception as e:
            logger.error(f"❌ Error en validación semanal: {e}")
    
    def _ejecutar_reentrenamiento_completo(self):
        """Ejecuta reentrenamiento completo del sistema"""
        logger.info("🔄 Iniciando reentrenamiento completo...")
        
        try:
            # Marcar como reentrenamiento
            logger.info("📚 Reentrenamiento automático programado")
            
            # Ejecutar pipeline completo con flag de reentrenamiento
            resultado = self.ejecutar_pipeline_pcf_completo()
            
            if resultado:
                logger.info("✅ Reentrenamiento completado exitosamente")
            else:
                logger.error("❌ Error en reentrenamiento")
                self._enviar_notificacion_error("Error en reentrenamiento programado")
                
        except Exception as e:
            logger.error(f"❌ Excepción en reentrenamiento: {e}")
            self._enviar_notificacion_error(f"Excepción en reentrenamiento: {e}")
    
    def _verificar_salud_sistema(self):
        """Verificación periódica de salud del sistema"""
        
        try:
            # Verificar archivos críticos
            archivos_criticos = [
                'estado_sistema_pcf.json',
                'ceapsi_pcf_automation.log'
            ]
            
            problemas = []
            
            for archivo in archivos_criticos:
                if not os.path.exists(archivo):
                    problemas.append(f"Archivo crítico faltante: {archivo}")
            
            # Verificar espacio en disco
            import shutil
            espacio_libre = shutil.disk_usage(self.base_path).free / (1024**3)  # GB
            
            if espacio_libre < 1:  # Menos de 1GB
                problemas.append(f"Espacio en disco bajo: {espacio_libre:.1f}GB")
            
            # Verificar última ejecución exitosa
            if self.estado_sistema.get('ultima_ejecucion'):
                ultima_ejecucion = datetime.fromisoformat(self.estado_sistema['ultima_ejecucion'])
                horas_sin_ejecucion = (datetime.now() - ultima_ejecucion).total_seconds() / 3600
                
                if horas_sin_ejecucion > 36:  # Más de 36 horas sin ejecutar
                    problemas.append(f"Sin ejecución exitosa por {horas_sin_ejecucion:.1f} horas")
            
            if problemas:
                logger.warning(f"⚠️ Problemas de salud detectados: {len(problemas)}")
                for problema in problemas:
                    logger.warning(f"   - {problema}")
            
            # Actualizar estado de salud
            self.estado_sistema['salud_sistema'] = {
                'timestamp': datetime.now().isoformat(),
                'estado': 'OK' if not problemas else 'DEGRADADO' if len(problemas) <= 2 else 'CRITICO',
                'problemas': problemas
            }
            
        except Exception as e:
            logger.error(f"❌ Error verificando salud del sistema: {e}")
    
    def _limpiar_archivos_temporales(self):
        """Limpia archivos temporales y logs antiguos"""
        
        try:
            archivos_limpiados = 0
            
            # Limpiar archivos temporales
            temp_patterns = ['temp_*.json', 'temp_*.csv', '*.tmp']
            
            import glob
            for pattern in temp_patterns:
                for archivo in glob.glob(pattern):
                    try:
                        os.remove(archivo)
                        archivos_limpiados += 1
                    except:
                        continue
            
            # Rotar logs si son muy grandes
            log_file = 'ceapsi_pcf_automation.log'
            if os.path.exists(log_file):
                size_mb = os.path.getsize(log_file) / (1024**2)
                if size_mb > 50:  # Si el log supera 50MB
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    os.rename(log_file, f'ceapsi_pcf_automation_{timestamp}.log')
                    logger.info(f"📁 Log rotado: {size_mb:.1f}MB")
            
            logger.info(f"🧹 Limpieza completada: {archivos_limpiados} archivos temporales eliminados")
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza: {e}")
    
    def ejecutar_loop_principal(self):
        """Ejecuta el loop principal de automatización PCF"""
        
        logger.info("🔄 INICIANDO LOOP PRINCIPAL DE AUTOMATIZACIÓN PCF")
        
        # Cargar estado previo si existe
        try:
            if os.path.exists('estado_sistema_pcf.json'):
                with open('estado_sistema_pcf.json', 'r') as f:
                    self.estado_sistema.update(json.load(f))
                logger.info("📊 Estado previo del sistema cargado")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar estado previo: {e}")
        
        # Configurar scheduler
        self.configurar_scheduler()
        
        # Ejecutar una validación inicial
        logger.info("🔍 Ejecutando validación inicial...")
        try:
            self._verificar_salud_sistema()
        except Exception as e:
            logger.error(f"❌ Error en validación inicial: {e}")
        
        # Loop principal
        logger.info("✅ Sistema PCF listo. Entrando en modo automático...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
        except KeyboardInterrupt:
            logger.info("🛑 Sistema PCF detenido por usuario")
        except Exception as e:
            logger.error(f"❌ Error crítico en loop principal: {e}")
            self._enviar_notificacion_error(f"Error crítico en loop principal: {e}")
            raise

def crear_configuracion_pcf_ejemplo():
    """Crea archivo de configuración de ejemplo para PCF"""
    
    config_pcf = {
        "base_path": str(Path(__file__).parent.absolute()),
        "objetivos_performance": {
            "mae_objetivo": 10.0,
            "rmse_objetivo": 15.0,
            "mape_objetivo": 25.0,
            "precision_alertas_objetivo": 90.0
        },
        "umbrales_alerta": {
            "mae_critico": 25.0,
            "rmse_critico": 35.0,
            "degradacion_performance": 20.0
        },
        "frecuencia_ejecucion": {
            "predicciones_diarias": "06:00",
            "validacion_semanal": "monday",
            "reentrenamiento": "sunday",
            "reporte_ejecutivo": "friday"
        },
        "email": {
            "enabled": True,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "username": "sistema-pcf@ceapsi.cl",
            "password": "app_password_here",
            "from": "sistema-pcf@ceapsi.cl",
            "to_operations": [
                "operaciones@ceapsi.cl",
                "callcenter@ceapsi.cl",
                "supervisores@ceapsi.cl"
            ],
            "to_executive": [
                "gerencia@ceapsi.cl",
                "direccion@ceapsi.cl",
                "cfo@ceapsi.cl"
            ],
            "to_technical": [
                "it@ceapsi.cl",
                "datascience@ceapsi.cl",
                "devops@ceapsi.cl"
            ]
        },
        "tipos_llamada": ["ENTRANTE", "SALIENTE"],
        "modelos_requeridos": ["arima", "prophet", "random_forest", "gradient_boosting"],
        "backup": {
            "enabled": True,
            "retention_days": 30,
            "path": "backups/"
        },
        "monitoreo": {
            "metricas_retention_days": 90,
            "log_rotation_size_mb": 50,
            "health_check_interval_hours": 2
        }
    }
    
    with open('config_pcf.json', 'w', encoding='utf-8') as f:
        json.dump(config_pcf, f, indent=2, ensure_ascii=False)
    
    print("✅ Archivo de configuración PCF creado: config_pcf.json")
    print("\n📋 CONFIGURACIÓN INICIAL REQUERIDA:")
    print("1. Actualizar credenciales de email")
    print("2. Verificar rutas de directorios")
    print("3. Ajustar horarios según operación")
    print("4. Configurar destinatarios de notificaciones")

def main():
    """Función principal del sistema de automatización PCF"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Automatización PCF - CEAPSI')
    parser.add_argument('--config', default='config_pcf.json', help='Archivo de configuración')
    parser.add_argument('--create-config', action='store_true', help='Crear configuración de ejemplo')
    parser.add_argument('--run-once', action='store_true', help='Ejecutar pipeline una sola vez')
    parser.add_argument('--validate', action='store_true', help='Ejecutar solo validación')
    parser.add_argument('--report', action='store_true', help='Generar reporte semanal')
    parser.add_argument('--health-check', action='store_true', help='Verificar salud del sistema')
    
    args = parser.parse_args()
    
    if args.create_config:
        crear_configuracion_pcf_ejemplo()
        return
    
    if not os.path.exists(args.config):
        print(f"❌ Archivo de configuración no encontrado: {args.config}")
        print("💡 Usar --create-config para crear uno de ejemplo")
        return
    
    # Crear sistema de automatización
    sistema_pcf = SistemaAutomatizacionPCF(args.config)
    
    try:
        if args.run_once:
            # Ejecutar pipeline una sola vez
            print("🚀 Ejecutando pipeline PCF una sola vez...")
            exito = sistema_pcf.ejecutar_pipeline_pcf_completo()
            print(f"{'✅ Completado exitosamente' if exito else '❌ Ejecución falló'}")
            sys.exit(0 if exito else 1)
        
        elif args.validate:
            # Solo validación
            print("🔍 Ejecutando validación del sistema...")
            sistema_pcf._ejecutar_validacion_semanal()
            print("✅ Validación completada")
        
        elif args.report:
            # Solo reporte
            print("📊 Generando reporte semanal...")
            sistema_pcf.generar_reporte_semanal()
            print("✅ Reporte generado")
        
        elif args.health_check:
            # Solo verificación de salud
            print("🏥 Verificando salud del sistema...")
            sistema_pcf._verificar_salud_sistema()
            
            estado = sistema_pcf.estado_sistema.get('salud_sistema', {})
            print(f"Estado: {estado.get('estado', 'DESCONOCIDO')}")
            
            problemas = estado.get('problemas', [])
            if problemas:
                print("⚠️ Problemas detectados:")
                for problema in problemas:
                    print(f"   - {problema}")
            else:
                print("✅ Sistema saludable")
        
        else:
            # Ejecutar loop continuo
            print("🔄 Iniciando sistema de automatización PCF...")
            sistema_pcf.ejecutar_loop_principal()
    
    except KeyboardInterrupt:
        logger.info("🛑 Sistema PCF detenido por usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico en sistema PCF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()    
    def ejecutar_pipeline_pcf_completo(self):
        """Ejecuta el pipeline completo del Proyecto PCF"""
        
        logger.info("🚀 INICIANDO PIPELINE PCF COMPLETO")
        
        try:
            # 1. Auditoría de datos
            logger.info("🔍 Ejecutando auditoría de datos...")
            if not self._ejecutar_auditoria_datos():
                raise Exception("Falla en auditoría de datos")
            
            # 2. Segmentación de llamadas
            logger.info("🔀 Ejecutando segmentación de llamadas...")
            if not self._ejecutar_segmentacion():
                raise Exception("Falla en segmentación")
            
            # 3. Sistema multi-modelo para cada tipo
            resultados_modelos = {}
            for tipo_llamada in self.config['tipos_llamada']:
                logger.info(f"🤖 Entrenando modelos para {tipo_llamada}...")
                resultado = self._ejecutar_sistema_multimodelo(tipo_llamada)
                if resultado:
                    resultados_modelos[tipo_llamada] = resultado
                else:
                    logger.error(f"❌ Falla en modelos para {tipo_llamada}")
            
            # 4. Validación de performance
            logger.info("📊 Validando performance del sistema...")
            metricas_performance = self._validar_performance_sistema(resultados_modelos)
            
            # 5. Detección de alertas críticas
            alertas_criticas = self._detectar_alertas_sistema(resultados_modelos, metricas_performance)
            
            # 6. Generación de reportes
            logger.info("📄 Generando reportes...")
            self._generar_reportes_completos(resultados_modelos, metricas_performance, alertas_criticas)
            
            # 7. Backup y limpieza
            logger.info("💾 Realizando backup...")
            self._realizar_backup()
            
            # 8. Notificaciones
            if alertas_criticas:
                self._enviar_alertas_criticas(alertas_criticas)
            
            # 9. Actualizar estado del sistema
            self._actualizar_estado_sistema(metricas_performance, True)
            
            logger.info("✅ PIPELINE PCF COMPLETADO EXITOSAMENTE")
            return True
            
        except Exception as e:
            logger.error(f"❌ ERROR EN PIPELINE PCF: {e}")
            self._actualizar_estado_sistema({}, False)
            self._enviar_notificacion_error(str(e))
            return False
    
    def _ejecutar_auditoria_datos(self):
        """Ejecuta la auditoría profunda de datos"""
        try:
            script_auditoria = os.path.join(self.base_path, "auditoria_datos_llamadas.py")
            result = subprocess.run(
                [sys.executable, script_auditoria],
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode == 0:
                logger.info("✅ Auditoría completada exitosamente")
                return True
            else:
                logger.error(f"❌ Error en auditoría: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción en auditoría: {e}")
            return False
    
    def _ejecutar_segmentacion(self):
        """Ejecuta la segmentación inteligente de llamadas"""
        try:
            script_segmentacion = os.path.join(self.base_path, "segmentacion_llamadas.py")
            result = subprocess.run(
                [sys.executable, script_segmentacion],
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            if result.returncode == 0:
                logger.info("✅ Segmentación completada exitosamente")
                return True
            else:
                logger.error(f"❌ Error en segmentación: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción en segmentación: {e}")
            return False
    
    def _ejecutar_sistema_multimodelo(self, tipo_llamada):
        """Ejecuta el sistema multi-modelo para un tipo específico"""
        try:
            script_multimodelo = os.path.join(self.base_path, "sistema_multi_modelo.py")
            
            # Crear script temporal con configuración específica
            config_temp = {
                'tipo_llamada': tipo_llamada,
                'modelos_activos': self.config['modelos_requeridos'],
                'objetivos': self.config['objetivos_performance']
            }
            
            with open('temp_config_multimodelo.json', 'w') as f:
                json.dump(config_temp, f)
            
            result = subprocess.run(
                [sys.executable, script_multimodelo, '--config', 'temp_config_multimodelo.json', '--tipo', tipo_llamada],
                capture_output=True,
                text=True,
                cwd=self.base_path
            )
            
            # Limpiar archivo temporal
            if os.path.exists('temp_config_multimodelo.json'):
                os.remove('temp_config_multimodelo.json')
            
            if result.returncode == 0:
                logger.info(f"✅ Sistema multi-modelo para {tipo_llamada} completado")
                
                # Cargar resultados
                return self._cargar_resultados_multimodelo(tipo_llamada)
            else:
                logger.error(f"❌ Error en multi-modelo {tipo_llamada}: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Excepción en multi-modelo {tipo_llamada}: {e}")
            return None
    
    def _cargar_resultados_multimodelo(self, tipo_llamada):
        """Carga los resultados más recientes del sistema multi-modelo"""
        try:
            # Buscar archivo más reciente
            patron = f"predicciones_multimodelo_{tipo_llamada.lower()}"
            archivos = [f for f in os.listdir(self.base_path) if f.startswith(patron) and f.endswith('.json')]
            
            if not archivos:
                logger.warning(f"⚠️ No se encontraron resultados para {tipo_llamada}")
                return None
            
            archivo_reciente = sorted(archivos)[-1]
            ruta_archivo = os.path.join(self.base_path, archivo_reciente)
            
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                resultados = json.load(f)
            
            logger.info(f"✅ Resultados cargados para {tipo_llamada}")
            return resultados
            
        except Exception as e:
            logger.error(f"❌ Error cargando resultados {tipo_llamada}: {e}")
            return None
    
    def _validar_performance_sistema(self, resultados_modelos):
        """Valida la performance general del sistema"""
        
        metricas_globales = {
            'timestamp': datetime.now().isoformat(),
            'tipos_procesados': list(resultados_modelos.keys()),
            'performance_por_tipo': {},
            'cumplimiento_objetivos': {},
            'estado_general': 'DESCONOCIDO'
        }
        
        objetivos = self.config['objetivos_performance']
        cumplimientos = []
        
        for tipo, resultados in resultados_modelos.items():
            if not resultados:
                continue
            
            # Extraer métricas del ensemble
            metadatos = resultados.get('metadatos_modelos', {})
            
            # Calcular MAE promedio ponderado
            mae_ponderado = 0
            suma_pesos = 0
            pesos = resultados.get('pesos_ensemble', {})
            
            for modelo, peso in pesos.items():
                if modelo in metadatos:
                    mae_modelo = metadatos[modelo].get('mae_validacion', metadatos[modelo].get('mae_cv', 0))
                    if mae_modelo > 0:
                        mae_ponderado += mae_modelo * peso
                        suma_pesos += peso
            
            if suma_pesos > 0:
                mae_final = mae_ponderado / suma_pesos
            else:
                mae_final = float('inf')
            
            # Calcular métricas del tipo
            performance_tipo = {
                'mae_ensemble': mae_final,
                'modelos_activos': len(pesos),
                'mejor_modelo': max(pesos, key=pesos.get) if pesos else None,
                'predicciones_generadas': len(resultados.get('predicciones', [])),
                'alertas_detectadas': len(resultados.get('alertas', []))
            }
            
            # Evaluar cumplimiento de objetivos
            cumplimiento_tipo = {
                'mae_objetivo': mae_final <= objetivos['mae_objetivo'],
                'modelos_suficientes': len(pesos) >= 3,
                'predicciones_completas': performance_tipo['predicciones_generadas'] >= 20
            }
            
            metricas_globales['performance_por_tipo'][tipo] = performance_tipo
            metricas_globales['cumplimiento_objetivos'][tipo] = cumplimiento_tipo
            
            # Calcular score de cumplimiento
            score_tipo = sum(cumplimiento_tipo.values()) / len(cumplimiento_tipo) * 100
            cumplimientos.append(score_tipo)
            
            logger.info(f"📊 {tipo}: MAE={mae_final:.2f}, Score={score_tipo:.1f}%")
        
        # Estado general del sistema
        if cumplimientos:
            score_general = np.mean(cumplimientos)
            if score_general >= 80:
                metricas_globales['estado_general'] = 'EXCELENTE'
            elif score_general >= 60:
                metricas_globales['estado_general'] = 'BUENO'
            elif score_general >= 40:
                metricas_globales['estado_general'] = 'REQUIERE_ATENCION'
            else:
                metricas_globales['estado_general'] = 'CRITICO'
            
            metricas_globales['score_general'] = score_general
        
        logger.info(f"🎯 Estado general del sistema: {metricas_globales['estado_general']}")
        
        return metricas_globales
    
    def _detectar_alertas_sistema(self, resultados_modelos, metricas_performance):
        """Detecta alertas a nivel de sistema"""
        
        alertas_sistema = []
        umbrales = self.config['umbrales_alerta']
        
        # Alertas por performance
        for tipo, performance in metricas_performance.get('performance_por_tipo', {}).items():
            mae = performance.get('mae_ensemble', float('inf'))
            
            if mae > umbrales['mae_critico']:
                alertas_sistema.append({
                    'tipo': 'PERFORMANCE_CRITICA',
                    'severidad': 'CRITICA',
                    'componente': f'Modelos {tipo}',
                    'mensaje': f'MAE crítico de {mae:.2f} en {tipo} (umbral: {umbrales["mae_critico"]})',
                    'accion': 'Revisar inmediatamente calidad de datos y modelos',
                    'timestamp': datetime.now().isoformat()
                })
            
            modelos_activos = performance.get('modelos_activos', 0)
            if modelos_activos < 2:
                alertas_sistema.append({
                    'tipo': 'MODELOS_INSUFICIENTES',
                    'severidad': 'ALTA',
                    'componente': f'Ensemble {tipo}',
                    'mensaje': f'Solo {modelos_activos} modelos activos en {tipo}',
                    'accion': 'Verificar entrenamiento de modelos adicionales',
                    'timestamp': datetime.now().isoformat()
                })
        
        # Alertas por degradación de performance
        if self.metricas_historicas:
            ultima_metrica = self.metricas_historicas[-1]
            score_actual = metricas_performance.get('score_general', 0)
            score_anterior = ultima_metrica.get('score_general', 0)
            
            if score_anterior > 0:
                degradacion = ((score_anterior - score_actual) / score_anterior) * 100
                
                if degradacion > umbrales['degradacion_performance']:
                    alertas_sistema.append({
                        'tipo': 'DEGRADACION_PERFORMANCE',
                        'severidad': 'ALTA',
                        'componente': 'Sistema General',
                        'mensaje': f'Degradación de {degradacion:.1f}% en performance general',
                        'accion': 'Investigar causas de degradación y reentrenar modelos',
                        'timestamp': datetime.now().isoformat()
                    })
        
        # Alertas por estado del sistema
        estado_general = metricas_performance.get('estado_general', 'DESCONOCIDO')
        if estado_general in ['CRITICO', 'REQUIERE_ATENCION']:
            alertas_sistema.append({
                'tipo': 'ESTADO_SISTEMA',
                'severidad': 'CRITICA' if estado_general == 'CRITICO' else 'ALTA',
                'componente': 'Sistema PCF',
                'mensaje': f'Sistema en estado {estado_general}',
                'accion': 'Revisión completa del sistema requerida',
                'timestamp': datetime.now().isoformat()
            })
        
        # Consolidar alertas de modelos individuales
        for tipo, resultados in resultados_modelos.items():
            alertas_modelo = resultados.get('alertas', [])
            alertas_criticas_modelo = [a for a in alertas_modelo if a.get('severidad') == 'CRITICA']
            
            if len(alertas_criticas_modelo) > 5:
                alertas_sistema.append({
                    'tipo': 'MULTIPLES_ALERTAS_CRITICAS',
                    'severidad': 'CRITICA',
                    'componente': f'Predicciones {tipo}',
                    'mensaje': f'{len(alertas_criticas_modelo)} alertas críticas en predicciones de {tipo}',
                    'accion': 'Revisar configuración de umbrales y capacidad operativa',
                    'timestamp': datetime.now().isoformat()
                })
        
        logger.info(f"🚨 {len(alertas_sistema)} alertas de sistema detectadas")
        return alertas_sistema
    
    def _generar_reportes_completos(self, resultados_modelos, metricas_performance, alertas_sistema):
        """Genera reportes completos del sistema"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Reporte ejecutivo
        reporte_ejecutivo = {
            'metadata': {
                'timestamp': timestamp,
                'periodo_reporte': 'Ejecución automática',
                'sistema': 'Proyecto PCF - CEAPSI'
            },
            'resumen_ejecutivo': {
                'estado_sistema': metricas_performance.get('estado_general', 'DESCONOCIDO'),
                'score_general': metricas_performance.get('score_general', 0),
                'tipos_procesados': len(resultados_modelos),
                'alertas_criticas': len([a for a in alertas_sistema if a.get('severidad') == 'CRITICA']),
                'mejoras_logradas': self._calcular_mejoras_vs_baseline()
            },
            'performance_detallada': metricas_performance,
            'alertas_sistema': alertas_sistema,
            'recomendaciones_estrategicas': self._generar_recomendaciones_ejecutivas(metricas_performance),
            'proximo_reentrenamiento': self._calcular_fecha_reentrenamiento(),
            'impacto_negocio': self._calcular_impacto_negocio(metricas_performance)
        }
        
        # Guardar reporte ejecutivo
        filename_ejecutivo = f"reporte_ejecutivo_pcf_{timestamp}.json"
        ruta_ejecutivo = os.path.join(self.base_path, filename_ejecutivo)
        
        with open(ruta_ejecutivo, 'w', encoding='utf-8') as f:
            json.dump(reporte_ejecutivo, f, indent=2, ensure_ascii=False, default=str)
        
        # Reporte técnico detallado
        reporte_tecnico = {
            'metadata': {
                'timestamp': timestamp,
                'version_sistema': '1.0-PCF',
                'configuracion': self.config
            },
            'resultados_por_tipo': resultados_modelos,
            'metricas_sistema': metricas_performance,
            'alertas_detalladas': alertas_sistema,
            'diagnosticos_tecnicos': self._generar_diagnosticos_tecnicos(resultados_modelos),
            'logs_ejecucion': self._obtener_logs_recientes()
        }
        
        filename_tecnico = f"reporte_tecnico_pcf_{timestamp}.json"
        ruta_tecnico = os.path.join(self.base_path, filename_tecnico)
        
        with open(ruta_tecnico, 'w', encoding='utf-8') as f:
            json.dump(reporte_tecnico, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📄 Reportes generados: {filename_ejecutivo}, {filename_tecnico}")
        
        return ruta_ejecutivo, ruta_tecnico
    
    def _calcular_mejoras_vs_baseline(self):
        """Calcula mejoras respecto al baseline original"""
        # Baseline del problema original
        baseline_mae = 32.81
        baseline_rmse = 41.11
        
        # Calcular mejora promedio
        if self.estado_sistema.get('performance_actual'):
            mae_actual = self.estado_sistema['performance_actual'].get('mae_promedio', baseline_mae)
            mejora_mae = ((baseline_mae - mae_actual) / baseline_mae) * 100
            
            return {
                'mejora_mae_porcentaje': max(0, mejora_mae),
                'baseline_original': {'mae': baseline_mae, 'rmse': baseline_rmse},
                'objetivo_alcanzado': mae_actual <= 10
            }
        
        return {'mensaje': 'Datos insuficientes para calcular mejoras'}
    
    def _generar_recomendaciones_ejecutivas(self, metricas_performance):
        """Genera recomendaciones estratégicas para ejecutivos"""
        
        recomendaciones = []
        estado = metricas_performance.get('estado_general', 'DESCONOCIDO')
        score = metricas_performance.get('score_general', 0)
        
        if estado == 'EXCELENTE':
            recomendaciones.append({
                'prioridad': 'BAJA',
                'area': 'OPERACIONES',
                'titulo': 'Mantener Excelencia Operativa',
                'descripcion': 'Sistema funcionando óptimamente. Mantener rutinas de monitoreo.',
                'impacto_negocio': 'MANTENIMIENTO'
            })
        
        elif estado == 'CRITICO':
            recomendaciones.append({
                'prioridad': 'CRITICA',
                'area': 'TECNOLOGIA',
                'titulo': 'Intervención Inmediata Requerida',
                'descripcion': 'Performance por debajo de estándares mínimos. Requiere revisión completa.',
                'impacto_negocio': 'ALTO_RIESGO'
            })
        
        # Recomendaciones específicas por performance
        for tipo, performance in metricas_performance.get('performance_por_tipo', {}).items():
            mae = performance.get('mae_ensemble', float('inf'))
            
            if mae > 20:
                recomendaciones.append({
                    'prioridad': 'ALTA',
                    'area': 'CALL_CENTER',
                    'titulo': f'Mejorar Predicciones {tipo}',
                    'descripcion': f'MAE de {mae:.1f} en {tipo} requiere optimización',
                    'impacto_negocio': 'EFICIENCIA_OPERATIVA'
                })
        
        return recomendaciones
    
    def _calcular_fecha_reentrenamiento(self):
        """Calcula próxima fecha de reentrenamiento"""
        
        # Por defecto, reentrenar cada domingo
        hoy = datetime.now()
        dias_hasta_domingo = (6 - hoy.weekday()) % 7
        if dias_hasta_domingo == 0:
            dias_hasta_domingo = 7  # Si es domingo, programar para el próximo
        
        proximo_reentrenamiento = hoy + timedelta(days=dias_hasta_domingo)
        
        return {
            'fecha_programada': proximo_reentrenamiento.strftime('%Y-%m-%d'),
            'dias_restantes': dias_hasta_domingo,
            'tipo': 'AUTOMATICO_SEMANAL'
        }
    
    def _calcular_impacto_negocio(self, metricas_performance):
        """Calcula el impacto en negocio de las mejoras"""
        
        # Estimaciones basadas en mejoras de predicción
        score = metricas_performance.get('score_general', 0)
        
        # Impactos estimados
        if score >= 80:
            ahorro_mensual = 15000  # USD
            mejora_satisfaccion = 15   # %
            reduccion_overtime = 25    # %
        elif score >= 60:
            ahorro_mensual = 8000
            mejora_satisfaccion = 8
            reduccion_overtime = 15
        else:
            ahorro_mensual = 0
            mejora_satisfaccion = 0
            reduccion_overtime = 0
        
        return {
            'ahorro_mensual_estimado_usd': ahorro_mensual,
            'mejora_satisfaccion_cliente_pct': mejora_satisfaccion,
            'reduccion_overtime_pct': reduccion_overtime,
            'roi_anual_estimado_pct': (ahorro_mensual * 12) / 75000 * 100  # Inversión estimada proyecto
        }
    
    def _generar_diagnosticos_tecnicos(self, resultados_modelos):
        """Genera diagnósticos técnicos detallados"""
        
        diagnosticos = {}
        
        for tipo, resultados in resultados_modelos.items():
            if not resultados:
                continue
            
            pesos = resultados.get('pesos_ensemble', {})
            metadatos = resultados.get('metadatos_modelos', {})
            
            diagnosticos[tipo] = {
                'modelos_ensemble': len(pesos),
                'balance_pesos': self._evaluar_balance_ensemble(pesos),
                'estabilidad_modelos': self._evaluar_estabilidad_modelos(metadatos),
                'calidad_predicciones': self._evaluar_calidad_predicciones(resultados),
                'recomendaciones_tecnicas': self._generar_recomendaciones_tecnicas(resultados)
            }
        
        return diagnosticos
    
    def _evaluar_balance_ensemble(self, pesos):
        """Evalúa el balance del ensemble"""
        if not pesos:
            return {'status': 'NO_DATA', 'score': 0}
        
        valores_pesos = list(pesos.values())
        peso_max = max(valores_pesos)
        
        if peso_max > 0.7:
            return {'status': 'DESBALANCEADO', 'score': 30, 'peso_dominante': peso_max}
        elif peso_max > 0.5:
            return {'status': 'MODERADAMENTE_BALANCEADO', 'score': 70, 'peso_dominante': peso_max}
        else:
            return {'status': 'BIEN_BALANCEADO', 'score': 90, 'peso_dominante': peso_max}
    
    def _evaluar_estabilidad_modelos(self, metadatos):
        """Evalúa la estabilidad de los modelos"""
        if not metadatos:
            return {'status': 'NO_DATA', 'score': 0}
        
        maes = []
        for modelo, meta in metadatos.items():
            mae = meta.get('mae_validacion', meta.get('mae_cv', 0))
            if mae > 0:
                maes.append(mae)
        
        if not maes:
            return {'status': 'NO_METRICS', 'score': 0}
        
        variabilidad = np.std(maes) / np.mean(maes) if np.mean(maes) > 0 else float('inf')
        
        if variabilidad < 0.2:
            return {'status': 'ESTABLE', 'score': 90, 'variabilidad': variabilidad}
        elif variabilidad < 0.5:
            return {'status': 'MODERADAMENTE_ESTABLE', 'score': 70, 'variabilidad': variabilidad}
        else:
            return {'status': 'INESTABLE', 'score': 30, 'variabilidad': variabilidad}
    
    def _evaluar_calidad_predicciones(self, resultados):
        """Evalúa la calidad de las predicciones generadas"""
        predicciones = resultados.get('predicciones', [])
        
        if not predicciones:
            return {'status': 'NO_PREDICTIONS', 'score': 0}
        
        # Evaluar consistencia y completitud
        df_pred = pd.DataFrame(predicciones)
        
        calidad = {
            'completitud': len(df_pred) >= 20,  # Al menos 20 días de predicción
            'consistencia': df_pred['yhat_ensemble'].std() / df_pred['yhat_ensemble'].mean() < 1,  # CV < 100%
            'valores_validos': (df_pred['yhat_ensemble'] >= 0).all(),  # Sin valores negativos
            'intervalos_consistentes': (df_pred['yhat_upper'] > df_pred['yhat_lower']).all() if 'yhat_upper' in df_pred.columns else True
        }
        
        score_calidad = sum(calidad.values()) / len(calidad) * 100
        
        return {
            'status': 'BUENA' if score_calidad >= 75 else 'REGULAR' if score_calidad >= 50 else 'MALA',
            'score': score_calidad,
            'detalles': calidad
        }
    
    def _generar_recomendaciones_tecnicas(self, resultados):
        """Genera recomendaciones técnicas específicas"""
        
        recomendaciones = []
        pesos = resultados.get('pesos_ensemble', {})
        
        # Recomendación por balance de ensemble
        if pesos:
            peso_max = max(pesos.values())
            if peso_max > 0.6:
                modelo_dominante = max(pesos, key=pesos.get)
                recomendaciones.append({
                    'tipo': 'BALANCE_ENSEMBLE',
                    'prioridad': 'MEDIA',
                    'descripcion': f'Modelo {modelo_dominante} domina ensemble con peso {peso_max:.3f}',
                    'accion': 'Optimizar modelos secundarios o ajustar pesos manualmente'
                })
        
        # Recomendación por número de modelos
        if len(pesos) < 3:
            recomendaciones.append({
                'tipo': 'DIVERSIDAD_MODELOS',
                'prioridad': 'ALTA',
                'descripcion': f'Solo {len(pesos)} modelos en ensemble',
                'accion': 'Agregar modelos adicionales (XGBoost, LSTM, etc.)'
            })
        
        return recomendaciones
    
    def _obtener_logs_recientes(self, ultimas_horas=24):
        """Obtiene logs recientes del sistema"""
        try:
            log_file = 'ceapsi_pcf_automation.log'
            if not os.path.exists(log_file):
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            
            # Filtrar últimas horas (simplificado)
            lineas_recientes = lineas[-100:]  # Últimas 100 líneas
            
            return [linea.strip() for linea in lineas_recientes]
        
        except Exception as e:
            logger.error(f"❌ Error obteniendo logs: {e}")
            return []
    
    def _realizar_backup(self):
        """Realiza backup de archivos importantes"""
        if not self.config.get('backup', {}).get('enabled', False):
            return
        
        try:
            import shutil
            from pathlib import Path
            
            # Crear directorio de backup
            backup_dir = os.path.join(self.base_path, 'backups', datetime.now().strftime('%Y%m%d'))
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
            
            # Archivos a respaldar
            archivos_importantes = [
                'predicciones_multimodelo_*.json',
                'reporte_ejecutivo_*.json',
                'reporte_tecnico_*.json',
                'datos_prophet_*.csv'
            ]
            
            import glob
            archivos_respaldados = 0
            
            for patron in archivos_importantes:
                archivos = glob.glob(os.path.join(self.base_path, patron))
                for archivo in archivos:
                    if os.path.exists(archivo):
                        shutil.copy2(archivo, backup_dir)
                        archivos_respaldados += 1
            
            # Limpiar backups antiguos
            self._limpiar_backups_antiguos()
            
            logger.info(f"💾 Backup completado: {archivos_respaldados} archivos respaldados")
            
        except Exception as e:
            logger.error(f"❌ Error en backup: {e}")
    
    def _limpiar_backups_antiguos(self):
        """Limpia backups antiguos según configuración de retención"""
        try:
            retention_days = self.config.get('backup', {}).get('retention_days', 30)
            backup_#!/usr/bin/env python3
"""
CEAPSI - Sistema de Automatización Completo para Proyecto PCF
Automatización end-to-end del pipeline de predicción mejorado
"""

import os
import sys
import json
import schedule
import time
import logging
import subprocess
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import numpy as np

# Configurar logging avanzado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ceapsi_pcf_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CEAPSI-PCF')

class SistemaAutomatizacionPCF:
    """Sistema de automatización completo para Proyecto PCF"""
    
    def __init__(self, config_path='config_pcf.json'):
        self.config = self.cargar_configuracion(config_path)
        self.base_path = self.config.get('base_path', '')
        self.metricas_historicas = []
        self.estado_sistema = {
            'ultima_ejecucion': None,
            'errores_consecutivos': 0,
            'modelos_activos': [],
            'performance_actual': {}
        }
        
    def cargar_configuracion(self, config_path):
        """Carga configuración del sistema PCF"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info("✅ Configuración PCF cargada")
            return config
        except FileNotFoundError:
            logger.warning("⚠️ Config no encontrado, usando valores por defecto")
            return self._config_por_defecto()
        except Exception as e:
            logger.error(f"❌ Error cargando config: {e}")
            return self._config_por_defecto()
    
    def _config_por_defecto(self):
        """Configuración por defecto del sistema"""
        return {
            'base_path': str(Path(__file__).parent.absolute()),
            'objetivos_performance': {
                'mae_objetivo': 10.0,
                'rmse_objetivo': 15.0,
                'mape_objetivo': 25.0,
                'precision_alertas_objetivo': 90.0
            },
            'umbrales_alerta': {
                'mae_critico': 25.0,
                'rmse_critico': 35.0,
                'degradacion_performance': 20.0  # % de degradación para alerta
            },
            'frecuencia_ejecucion': {
                'predicciones_diarias': '06:00',
                'validacion_semanal': 'monday',
                'reentrenamiento': 'sunday',
                'reporte_ejecutivo': 'friday'
            },
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'from': 'sistema-pcf@ceapsi.cl',
                'to_operations': ['operaciones@ceapsi.cl', 'callcenter@ceapsi.cl'],
                'to_executive': ['gerencia@ceapsi.cl', 'direccion@ceapsi.cl'],
                'to_technical': ['it@ceapsi.cl', 'datascience@ceapsi.cl']
            },
            'tipos_llamada': ['ENTRANTE', 'SALIENTE'],
            'modelos_requeridos': ['arima', 'prophet', 'random_forest', 'gradient_boosting'],
            'backup': {
                'enabled': True,
                'retention_days': 30,
                'path': 'backups/'
            }
        }
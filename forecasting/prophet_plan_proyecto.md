**Para Tableau:**

```python
# tableau_integration.py
def preparar_datos_tableau():
    """Prepara datos optimizados para Tableau"""
    
    engine = create_engine('postgresql://user:pass@localhost/ceapsi_forecast')
    
    # Query con cálculos adicionales para Tableau
    query_tableau = """
    SELECT 
        p.fecha_prediccion,
        p.horas_persona_necesarias,
        p.intervalo_inferior,
        p.intervalo_superior,
        EXTRACT(DOW FROM p.fecha_prediccion) as dia_semana_num,
        CASE EXTRACT(DOW FROM p.fecha_prediccion)
            WHEN 1 THEN 'Lunes'
            WHEN 2 THEN 'Martes'
            WHEN 3 THEN 'Miércoles'
            WHEN 4 THEN 'Jueves'
            WHEN 5 THEN 'Viernes'
            WHEN 6 THEN 'Sábado'
        END as dia_semana_nombre,
        EXTRACT(WEEK FROM p.fecha_prediccion) as semana_ano,
        EXTRACT(MONTH FROM p.fecha_prediccion) as mes,
        p.horas_persona_necesarias - LAG(p.horas_persona_necesarias, 7) 
            OVER (ORDER BY p.fecha_prediccion) as cambio_vs_semana_anterior,
        CASE 
            WHEN p.horas_persona_necesarias > 50 THEN 'Alta Demanda'
            WHEN p.horas_persona_necesarias > 35 THEN 'Demanda Media'
            ELSE 'Baja Demanda'
        END as categoria_demanda,
        ROW_NUMBER() OVER (ORDER BY p.fecha_prediccion) as orden_fecha
    FROM predicciones_personal p
    WHERE p.fecha_prediccion >= CURRENT_DATE - INTERVAL '30 days'
    ORDER BY p.fecha_prediccion
    """
    
    df_tableau = pd.read_sql(query_tableau, engine)
    
    # Exportar como Hyper para mejor rendimiento en Tableau
    from tableauhyperapi import HyperProcess, Telemetry, Connection, CreateMode
    
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hyper:
        with Connection(hyper.endpoint, 'predicciones_ceapsi.hyper', CreateMode.CREATE_AND_REPLACE) as connection:
            connection.execute_command(f"CREATE SCHEMA extract")
            
            # Crear tabla en Hyper
            table_def = TableDefinition(
                table_name=TableName("extract", "predicciones"),
                columns=[
                    TableDefinition.Column("fecha_prediccion", SqlType.date()),
                    TableDefinition.Column("horas_persona_necesarias", SqlType.double()),
                    TableDefinition.Column("intervalo_inferior", SqlType.double()),
                    TableDefinition.Column("intervalo_superior", SqlType.double()),
                    TableDefinition.Column("dia_semana_nombre", SqlType.text()),
                    TableDefinition.Column("categoria_demanda", SqlType.text())
                ]
            )
            
            connection.catalog.create_table(table_def)
            
            # Insertar datos
            with Inserter(connection, table_def) as inserter:
                for row in df_tableau.itertuples():
                    inserter.add_row([
                        row.fecha_prediccion,
                        row.horas_persona_necesarias,
                        row.intervalo_inferior,
                        row.intervalo_superior,
                        row.dia_semana_nombre,
                        row.categoria_demanda
                    ])
                inserter.execute()
    
    print("Archivo Hyper creado: predicciones_ceapsi.hyper")
    return df_tableau

# Plantilla de Workbook Tableau
tableau_template = """
CAMPOS CALCULADOS SUGERIDOS PARA TABLEAU:

1. Semana Actual:
   IF DATEPART('week', [Fecha Prediccion]) = DATEPART('week', TODAY()) 
   THEN "Semana Actual" ELSE "Otras Semanas" END

2. Días Hasta Predicción:
   DATEDIFF('day', TODAY(), [Fecha Prediccion])

3. Tendencia Semanal:
   WINDOW_AVG(SUM([Horas Persona Necesarias]), -6, 0)

4. Alerta Personal:
   IF [Horas Persona Necesarias] > 50 THEN "🔴 Contratar Personal Adicional"
   ELSEIF [Horas Persona Necesarias] > 35 THEN "🟡 Personal Estándar"
   ELSE "🟢 Considerar Reducir Turnos" END

5. Eficiencia Staffing:
   [Horas Persona Necesarias] / [Personal Disponible Estimado]

DASHBOARDS RECOMENDADOS:

Dashboard Ejecutivo:
- Filtros: Rango de fechas, Tipo de demanda
- KPI Cards: Horas próxima semana, Cambio vs anterior, Día pico
- Gráfico línea temporal: Tendencia 4 semanas
- Heatmap: Demanda por día de semana y semana
- Tabla: Top 5 días con mayor demanda

Dashboard Operativo:
- Filtros: Semana específica, Día de semana
- Gráfico barras: Distribución diaria
- Gráfico área: Intervalo de confianza
- Mapa de calor: Patrón semanal
- Alertas automáticas: Días que requieren acción
"""

print(tableau_template)
```

---

## **Resumen del Plan de Proyecto**

### **Cronograma de Implementación Sugerido**

| Fase | Duración | Entregables Clave |
|------|----------|-------------------|
| **Fase 1: Preparación** | 2-3 semanas | DataFrame unificado, regresores definidos |
| **Fase 2: Desarrollo** | 1-2 semanas | Modelo Prophet entrenado y validado |
| **Fase 3: Predicciones** | 1 semana | Pipeline de predicción funcionando |
| **Fase 4: Automatización** | 2-3 semanas | Sistema en producción automatizado |
| **Fase 5: Visualización** | 2 semanas | Dashboards ejecutivos operativos |

**Tiempo Total: 8-11 semanas**

### **Recursos Necesarios**

**Equipo Mínimo**:
- 1 Data Scientist Senior (Prophet, Python)
- 1 Data Engineer (ETL, Automatización)
- 1 Desarrollador Dashboard (Power BI/Tableau)
- 1 Product Owner (CEAPSI)

**Infraestructura**:
- Base de datos PostgreSQL o BigQuery
- Servidor Python (Cloud Functions o servidor dedicado)
- Herramienta BI (Power BI/Tableau)
- Sistema de monitoreo y alertas

### **Riesgos y Mitigaciones**

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Calidad de datos insuficiente | Media | Alto | Validación exhaustiva, datos sintéticos |
| Cambios en patrones operativos | Alta | Medio | Re-entrenamiento automático frecuente |
| Adopción baja por usuarios | Media | Alto | Training intensivo, UI intuitiva |
| Infraestructura inadecuada | Baja | Alto | Pruebas de carga, arquitectura escalable |

### **Métricas de Éxito**

**Técnicas**:
- MAE (Mean Absolute Error) < 10% en predicciones semanales
- Precisión en clasificación de demanda > 85%
- Tiempo de actualización < 30 minutos

**Negocio**:
- Reducción 20% en sobre-staffing
- Mejora 15% en satisfacción del paciente
- Optimización 25% en costos de personal

### **ROI Esperado**

**Inversión Estimada**: $50,000 - $80,000 USD
- Desarrollo: $40,000
- Infraestructura: $10,000
- Training/Change Management: $15,000

**Beneficios Anuales Estimados**: $150,000 - $200,000 USD
- Optimización personal: $100,000
- Mejora eficiencia operativa: $50,000
- Reducción overtime/temporales: $50,000

**ROI**: 200-300% en el primer año

---

## **Próximos Pasos Inmediatos**

1. **Validar datos históricos** - Verificar calidad y completitud de datos enero-junio 2025
2. **Definir regresores específicos** - Colaborar con operaciones para identificar variables predictivas
3. **Configurar entorno desarrollo** - Instalar Prophet, configurar acceso a datos
4. **Prototipo inicial** - Implementar versión básica con datos de muestra
5. **Validación con stakeholders** - Revisar outputs y ajustar según feedback

**Fecha de Inicio Sugerida**: Inmediata
**Primera Demo**: 2 semanas desde inicio
**MVP en Producción**: 6-8 semanas desde inicio

---

Este plan proporciona una hoja de ruta completa y detallada para implementar un sistema de forecasting robusto y automatizado que transformará la planificación de recursos humanos en CEAPSI, pasando de un enfoque reactivo a uno predictivo y basado en datos.

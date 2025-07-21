# Data Analysis Pipeline

Execute comprehensive data analysis and model training for call center predictions.

## Purpose

This command runs the complete CEAPSI data analysis pipeline including audit, segmentation, and multi-model training.

## Usage

```
/data-analysis
```

## What this command does

1. **Data Quality Audit** - Validates and analyzes uploaded data
2. **Call Segmentation** - Classifies incoming/outgoing calls
3. **Multi-Model Training** - Trains ARIMA, Prophet, RF, and GB models
4. **Performance Evaluation** - Measures MAE, RMSE, MAPE metrics
5. **Prediction Generation** - Creates 28-day forecasts

## Pipeline Commands

### Individual Module Execution
```bash
# Step 1: Data Quality Audit
python auditoria_datos_llamadas.py

# Step 2: Call Segmentation  
python segmentacion_llamadas.py

# Step 3: Multi-Model Training
python sistema_multi_modelo.py

# Step 4: Complete Automation (Optional)
python automatizacion_completa.py
```

### Full Pipeline Execution
```bash
# Complete automated pipeline
python start_ceapsi.py

# System verification
python verify_ceapsi.py

# Debug and repair if needed
python fix_ceapsi.py
```

## Data Requirements

### Input File Format
- **File types**: CSV (semicolon-separated), Excel (.xlsx, .xls)
- **Encoding**: UTF-8, Latin-1, or CP1252
- **Size limit**: Recommended < 200MB for optimal performance

### Required Columns
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| FECHA | DateTime | Call timestamp | 02-01-2023 08:08:07 |
| TELEFONO | String | Phone number | +56912345678 |
| SENTIDO | String | Call direction | 'in', 'out' |
| ATENDIDA | String | Answer status | 'Si', 'No' |

### Sample Data
Use the included `ejemplo_datos_llamadas.csv` for testing:
```csv
FECHA;TELEFONO;SENTIDO;ATENDIDA;STATUS
02-01-2023 08:08:07;+56912345678;in;Si;ANSWERED
02-01-2023 08:15:23;+56987654321;out;No;NO_ANSWER
```

## Analysis Modules

### 1. Data Audit (`auditoria_datos_llamadas.py`)
- **Data quality assessment** - Missing values, duplicates, outliers
- **Temporal pattern analysis** - Hourly, daily, weekly trends
- **Statistical summary** - Call volume distributions
- **Anomaly detection** - Unusual patterns or spikes
- **Output**: Diagnostic JSON report

### 2. Call Segmentation (`segmentacion_llamadas.py`)
- **Automatic classification** - Incoming vs outgoing calls
- **Pattern recognition** - Time-based calling patterns  
- **Confidence scoring** - Classification reliability metrics
- **Data splitting** - Separate datasets for model training
- **Output**: Segmented CSV files and analysis report

### 3. Multi-Model System (`sistema_multi_modelo.py`)
- **Model training**: ARIMA, Prophet, Random Forest, Gradient Boosting
- **Ensemble creation**: Weighted combination of models
- **Cross-validation**: Time series split validation
- **Performance evaluation**: MAE, RMSE, MAPE metrics
- **Output**: Trained models (.pkl) and predictions (.csv/.json)

### 4. Complete Automation (`automatizacion_completa.py`)
- **Scheduled execution**: Configurable timing
- **Email notifications**: Results and alerts
- **Error handling**: Automatic retry and recovery
- **Monitoring**: System health checks
- **Output**: Automated reports and logs

## Performance Objectives

The system targets these performance metrics:

| Metric | Target | Description |
|--------|---------|-------------|
| **MAE** | < 10 calls/day | Mean Absolute Error |
| **RMSE** | < 15 calls/day | Root Mean Square Error |
| **MAPE** | < 25% | Mean Absolute Percentage Error |
| **Alert Precision** | > 90% | Alert system accuracy |

## Output Files

### Generated Artifacts
- **Models**: `modelos_multimodelo_[type]_[timestamp].pkl`
- **Predictions**: `predicciones_multimodelo_[type]_[timestamp].csv/json`
- **Reports**: `diagnostico_llamadas_alodesk.json`
- **Segmentation**: `reporte_segmentacion_llamadas.json`
- **Logs**: `ceapsi_app.log`, `ceapsi_multimodelo.log`

### File Locations
All outputs are saved in the project directory with timestamps for version control.

## Troubleshooting

### Common Issues

**ModuleNotFoundError**
```bash
pip install -r requirements.txt
python verify_ceapsi.py
```

**Data Format Errors**
```bash
# Validate with sample data
python auditoria_datos_llamadas.py ejemplo_datos_llamadas.csv

# Check encoding issues
python -c "import pandas as pd; pd.read_csv('your_file.csv', sep=';', encoding='utf-8')"
```

**Model Training Failures**
```bash
# Check available memory
python -c "import psutil; print(f'Available RAM: {psutil.virtual_memory().available / 1024**3:.1f} GB')"

# Reduce data size or use sampling
python sistema_multi_modelo.py --sample 10000
```

**Performance Issues**
- Reduce dataset size for testing
- Use fewer models in ensemble
- Increase memory allocation
- Check disk space availability

## Monitoring

### Real-time Monitoring
```bash
# Monitor logs
tail -f ceapsi_app.log ceapsi_multimodelo.log

# Check system resources
htop  # Linux/Mac
taskmgr  # Windows
```

### Performance Validation
```bash
# Quick system check
python verify_ceapsi.py

# Detailed debugging
python debug/ceapsi_debugger.py
```

## Best Practices

1. **Data Preparation**
   - Clean data before analysis
   - Ensure consistent date formats
   - Remove or handle outliers appropriately

2. **Model Training**
   - Use sufficient historical data (minimum 30 days)
   - Validate results with holdout data
   - Monitor performance metrics regularly

3. **Production Deployment**
   - Schedule regular retraining
   - Monitor prediction accuracy
   - Set up automated alerts for anomalies
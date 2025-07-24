# Run Streamlit Dashboard

Launch the CEAPSI PCF Streamlit dashboard for interactive data analysis.

## Purpose

This command starts the main Streamlit application for the CEAPSI Precision Call Forecast system.

## Usage

```
/run-streamlit
```

## What this command does

1. **Starts Streamlit server** on default port (8501)
2. **Opens dashboard** in default browser
3. **Enables hot reload** for development
4. **Provides file upload interface** for data analysis
5. **Shows real-time predictions** and visualizations

## Command Details

```bash
# Start the main dashboard
streamlit run app.py

# Start with custom port
streamlit run app.py --server.port 8502

# Start without browser auto-open
streamlit run app.py --server.headless true
```

## Dashboard Features

### Main Sections
- **📊 Dashboard Validation**: Model comparison and predictions
- **🔍 Data Audit**: Automatic data quality analysis  
- **🔀 Call Segmentation**: Incoming/outgoing call classification
- **🤖 Multi-Model System**: AI model training and ensemble
- **⚙️ Complete Automation**: Scheduled pipeline execution

### File Upload Support
- **CSV files**: Semicolon-separated values
- **Excel files**: .xlsx and .xls formats
- **Encoding detection**: UTF-8, Latin-1, CP1252
- **Sample file**: `ejemplo_datos_llamadas.csv` included

### Required Data Columns
| Column | Description | Format |
|--------|-------------|--------|
| FECHA | Call timestamp | DD-MM-YYYY HH:MM:SS |
| TELEFONO | Phone number | +56912345678 |
| SENTIDO | Call direction | 'in' or 'out' |
| ATENDIDA | Call answered | 'Si' or 'No' |

## Performance Monitoring

The dashboard tracks these key metrics:
- **MAE**: Mean Absolute Error (target < 10)
- **RMSE**: Root Mean Square Error (target < 15)  
- **MAPE**: Mean Absolute Percentage Error (target < 25%)
- **Alert Precision**: Alert system accuracy (target > 90%)

## Troubleshooting

### Port Already in Use
```bash
# Kill existing Streamlit processes
taskkill /f /im streamlit.exe
# Or use different port
streamlit run app.py --server.port 8502
```

### Module Import Errors
```bash
# Install missing dependencies
pip install -r requirements.txt

# Verify system
python verify_ceapsi.py
```

### Data Upload Issues
- Check file format matches expected structure
- Ensure file size < 200MB for optimal performance
- Validate date format: DD-MM-YYYY HH:MM:SS
- Use provided sample file for testing

## Development Mode

For development with auto-reload:
```bash
# Enable debug mode
streamlit run app.py --server.runOnSave true

# Show additional debug info
streamlit run app.py --logger.level debug
```

## Access Information

Once started, the dashboard will be available at:
- **Local URL**: http://localhost:8501
- **Network URL**: http://[your-ip]:8501 (for network access)

## Logs and Debugging

Monitor these log files for troubleshooting:
- `ceapsi_app.log`: Main application logs
- `ceapsi_multimodelo.log`: Model training logs
- Browser console: Frontend debugging
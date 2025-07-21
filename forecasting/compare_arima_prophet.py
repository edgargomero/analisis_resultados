import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error
import os
import json
from datetime import datetime

# 1. Cargar datos
df = pd.read_csv('RUTA_A_TU_DATOS_PROPHET_CSV')  # Usa la ruta de la última carpeta de resultados
df['ds'] = pd.to_datetime(df['ds'])
df = df.sort_values('ds')

# 2. Separar entrenamiento y test (por ejemplo, últimos 28 días para test)
train = df.iloc[:-28]
test = df.iloc[-28:]

# 3. Prophet
m = Prophet()
m.fit(train[['ds', 'y']])
future = m.make_future_dataframe(periods=28)
forecast_prophet = m.predict(future)
pred_prophet = forecast_prophet[['ds', 'yhat']].set_index('ds').loc[test['ds']]

# 4. ARIMA (SARIMAX)
# Ajusta los parámetros (p,d,q) según tus datos, aquí un ejemplo simple:
model_arima = SARIMAX(train['y'], order=(1,1,1), seasonal_order=(1,1,1,7))
model_fit = model_arima.fit(disp=False)
pred_arima = model_fit.forecast(steps=28)
pred_arima.index = test['ds']

# 5. Comparar métricas
def print_metrics(y_true, y_pred, label):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    print(f"{label} - MAE: {mae:.2f}, RMSE: {rmse:.2f}")

print_metrics(test['y'], pred_prophet['yhat'], "Prophet")
print_metrics(test['y'], pred_arima, "ARIMA")

# 6. Graficar comparación
plt.figure(figsize=(12,6))
plt.plot(df['ds'], df['y'], label='Real', color='black')
plt.plot(test['ds'], pred_prophet['yhat'], label='Prophet', color='blue')
plt.plot(test['ds'], pred_arima, label='ARIMA', color='red')
plt.legend()
plt.title('Comparación Prophet vs ARIMA')
plt.xlabel('Fecha')
plt.ylabel('Horas-persona necesarias')
plt.show()

# Guardar predicciones ARIMA en la última carpeta de resultados
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
arima_pred_df = pd.DataFrame({
    'ds': test['ds'],
    'y_real': test['y'],
    'yhat_arima': pred_arima
})
ruta_ultima = os.path.join(os.path.dirname(__file__), "..", "resultados")
arima_pred_df.to_csv(f"{ruta_ultima}/predicciones_arima_{timestamp}.csv", index=False)
arima_pred_df.to_json(f"{ruta_ultima}/predicciones_arima_{timestamp}.json", orient='records', date_format='iso')
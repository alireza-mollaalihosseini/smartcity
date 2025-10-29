# smart_energy/src/forecasting.py
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
from sqlalchemy import create_engine
import joblib
import os

DB_URL = os.environ.get("ENERGY_DB_URL", "postgresql://admin:admin123@postgres.infrastructure.svc.cluster.local:5432/smartcity")

def load_data(engine, lookback_hours=24):
    q = f"SELECT * FROM energy_readings WHERE timestamp >= now() - interval '{lookback_hours} hours'"
    df = pd.read_sql(q, engine, parse_dates=["timestamp"])
    return df

def create_features(df, window=12):
    df = df.sort_values(["meter_id", "timestamp"])
    df["consumption_mean"] = df.groupby("meter_id")["consumption_kwh"].transform(lambda x: x.rolling(window).mean())
    df["consumption_std"] = df.groupby("meter_id")["consumption_kwh"].transform(lambda x: x.rolling(window).std())
    df["target_next"] = df.groupby("meter_id")["consumption_kwh"].shift(-1)  # predict next sample
    df = df.dropna()
    return df

def train_and_save():
    engine = create_engine(DB_URL)
    df = load_data(engine)
    if df.empty:
        print("No data")
        return
    df = create_features(df)
    features = ["consumption_mean", "consumption_std", "voltage", "frequency_hz"]
    X = df[features]
    y = df["target_next"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    print(f"Trained forecasting model. MAE: {mae:.4f}")
    os.makedirs("models", exist_ok=True)
    joblib.dump(model, "models/energy_forecast.pkl")
    print("Saved model to models/energy_forecast.pkl")

if __name__ == "__main__":
    train_and_save()

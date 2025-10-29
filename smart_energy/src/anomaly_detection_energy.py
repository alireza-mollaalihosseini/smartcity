# smart_energy/src/anomaly_detection_energy.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy import create_engine
import os

DB_URL = os.environ.get("ENERGY_DB_URL", "postgresql://admin:admin123@postgres.infrastructure.svc.cluster.local:5432/smartcity")

def read_recent(engine, minutes=60*24):
    q = f"SELECT * FROM energy_readings WHERE timestamp >= now() - interval '{minutes} minutes'"
    return pd.read_sql(q, engine, parse_dates=["timestamp"])

def detect_anomalies(df):
    # features: consumption, voltage, frequency + meter type encoded
    df = df.copy()
    features = ["consumption_kwh", "voltage", "frequency_hz"]
    X = df[features].fillna(0).values
    model = IsolationForest(contamination=0.01, random_state=42)
    df["anomaly_iforest"] = model.fit_predict(X)
    df["anomaly_iforest"] = df["anomaly_iforest"].map({1:0, -1:1})
    return df

def run_and_save():
    engine = create_engine(DB_URL)
    df = read_recent(engine, minutes=60*24)  # last 24h
    if df.empty:
        print("No data")
        return
    res = detect_anomalies(df)
    # For now, save anomalies locally or push to a table
    anomalies = res[res["anomaly_iforest"] == 1]
    print(f"Detected {len(anomalies)} anomalies")
    if not anomalies.empty:
        anomalies.to_csv("/tmp/energy_anomalies.csv", index=False)
        with engine.begin() as conn:
            anomalies.to_sql("energy_anomalies", conn, if_exists="append", index=False)
        print("Saved anomalies to DB and /tmp/energy_anomalies.csv")

if __name__ == "__main__":
    run_and_save()

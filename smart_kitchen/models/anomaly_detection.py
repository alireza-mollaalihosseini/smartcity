import os
import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of current file
    db_path = os.path.join(base_dir, "../data_pipeline/smart_kitchen.db")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM sensor_data", conn)
    conn.close()
    return df


def preprocess_data(df):
    # Sort by timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["device", "timestamp"])

    # Select numeric features for modeling
    features = ["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]
    X = df[features].values
    X_scaled = StandardScaler().fit_transform(X)
    return df, X_scaled


def detect_anomalies(df, X_scaled, contamination=0.03):
    # Isolation Forest is robust for unsupervised anomaly detection
    model = IsolationForest(contamination=contamination, random_state=42)
    df["anomaly"] = model.fit_predict(X_scaled)

    # Map -1 → anomaly, 1 → normal
    df["anomaly"] = df["anomaly"].map({1: 0, -1: 1})
    return df


def save_results(df, output_dir="results"):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "anomaly_results.csv")
    df.to_csv(output_path, index=False)
    print(f"✅ Anomaly detection results saved to {output_path}")


def run_anomaly_detection():
    df = load_data()
    df, X_scaled = preprocess_data(df)
    df = detect_anomalies(df, X_scaled)
    save_results(df)
    print(f"📊 Total anomalies detected: {df['anomaly'].sum()}")


if __name__ == "__main__":
    run_anomaly_detection()

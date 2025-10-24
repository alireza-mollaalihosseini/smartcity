import pandas as pd
from sklearn.ensemble import IsolationForest

def detect_anomalies(df):
    model = IsolationForest(contamination=0.05, random_state=42)
    features = df[["temperature", "co", "co2", "power"]]
    df["anomaly"] = model.fit_predict(features)
    anomalies = df[df["anomaly"] == -1]
    return anomalies

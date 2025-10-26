import os
import sqlite3
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # directory of current file
    db_path = os.path.join(base_dir, "../data_pipeline/smart_kitchen.db")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM sensor_data", conn)
    conn.close()
    return df


def create_features(df, target="temperature_C", window=5):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["device", "timestamp"])

    # Rolling window features
    df[f"{target}_mean"] = df.groupby("device")[target].transform(lambda x: x.rolling(window).mean())
    df[f"{target}_std"] = df.groupby("device")[target].transform(lambda x: x.rolling(window).std())
    df["power_mean"] = df.groupby("device")["power_W"].transform(lambda x: x.rolling(window).mean())
    df["CO_mean"] = df.groupby("device")["CO_ppm"].transform(lambda x: x.rolling(window).mean())
    df["CO2_mean"] = df.groupby("device")["CO2_ppm"].transform(lambda x: x.rolling(window).mean())

    # Predict next temperature (shifted)
    df["target_future_temp"] = df.groupby("device")[target].shift(-window)
    df = df.dropna()
    return df


def train_predictive_model(df):
    features = [col for col in df.columns if "mean" in col or "std" in col]
    X = df[features]
    y = df["target_future_temp"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"✅ Predictive maintenance model trained.")
    print(f"📊 MAE: {mae:.3f}, R²: {r2:.3f}")

    os.makedirs("saved_models", exist_ok=True)
    joblib.dump(model, "saved_models/predictive_maintenance.pkl")
    print(f"💾 Model saved at models/saved_models/predictive_maintenance.pkl")

    return model


def run_predictive_maintenance():
    df = load_data()
    df = create_features(df)
    model = train_predictive_model(df)


if __name__ == "__main__":
    run_predictive_maintenance()

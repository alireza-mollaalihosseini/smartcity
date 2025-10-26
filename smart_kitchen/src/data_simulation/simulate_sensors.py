import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
import requests
import json


# ======================================================
# Configuration
# ======================================================

DEVICES = {
    "refrigerator": {
        "temperature_range": (1, 8),
        "co_range": (0, 5),
        "co2_range": (300, 600),
        "power_range": (80, 200)
    },
    "oven": {
        "temperature_range": (150, 250),
        "co_range": (5, 15),
        "co2_range": (400, 800),
        "power_range": (1000, 2500)
    },
    "microwave": {
        "temperature_range": (50, 120),
        "co_range": (1, 10),
        "co2_range": (300, 700),
        "power_range": (600, 1200)
    }
}


# ======================================================
# Helper Functions
# ======================================================

def send_data_to_server(df, device_id, server_url="http://127.0.0.1:8000/upload_data"):
    # Convert timestamps safely to ISO format
    df = df.copy()
    df = df.applymap(lambda x: x.isoformat() if isinstance(x, pd.Timestamp) else x)

    # Prepare JSON payload
    payload = {
        "device_id": device_id,
        "readings": df.to_dict(orient="records")
    }

    try:
        response = requests.post(server_url, json=payload, timeout=10)
        response.raise_for_status()  # raise error if status != 200
        print(f"[→] Sent {len(df)} readings for {device_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[✗] Failed to send data for {device_id}: {e}")
    

def generate_normal_data(n_samples, base, noise_std):
    """Generate normally distributed sensor values."""
    return np.random.normal(loc=base, scale=noise_std, size=n_samples)


def inject_anomalies(values, anomaly_fraction=0.02, magnitude=3):
    """Randomly inject anomalies into a series."""
    n = len(values)
    n_anomalies = int(n * anomaly_fraction)
    indices = np.random.choice(n, n_anomalies, replace=False)
    for idx in indices:
        # Randomly choose whether to spike or drop
        if np.random.rand() > 0.5:
            values[idx] *= (1 + magnitude * np.random.rand())
        else:
            values[idx] *= (1 - magnitude * np.random.rand())
    return values


def simulate_device(device_name, n_samples=1440, freq="1min"):
    """Simulate data for a single device (1 day by default)."""
    np.random.seed(42)
    cfg = DEVICES[device_name]
    timestamps = pd.date_range(datetime.now(), periods=n_samples, freq=freq)

    data = {
        "timestamp": timestamps,
        "temperature": generate_normal_data(n_samples, np.mean(cfg["temperature_range"]), 1.0),
        "co": generate_normal_data(n_samples, np.mean(cfg["co_range"]), 0.5),
        "co2": generate_normal_data(n_samples, np.mean(cfg["co2_range"]), 10.0),
        "power": generate_normal_data(n_samples, np.mean(cfg["power_range"]), 10.0),
    }

    df = pd.DataFrame(data)
    df["device"] = device_name

    # Inject anomalies
    for col in ["temperature", "co", "co2", "power"]:
        df[col] = inject_anomalies(df[col].values, anomaly_fraction=0.01, magnitude=2)

    return df


def save_data(df, device_name, out_dir="../../data/raw/"):
    """Save simulated data to CSV."""
    os.makedirs(out_dir, exist_ok=True)
    filename = os.path.join(out_dir, f"{device_name}_data.csv")
    df.to_csv(filename, index=False)
    print(f"[✓] Saved simulated data for {device_name} → {filename}")


def simulate_all_devices(n_samples=1440):
    """Simulate and save data for all defined devices."""
    for device in DEVICES.keys():
        df = simulate_device(device, n_samples)
        save_data(df, device)
        send_data_to_server(df, device)


# ======================================================
# Main entry point
# ======================================================

if __name__ == "__main__":
    print("🔧 Simulating Smart Kitchen IoT data...")
    simulate_all_devices(n_samples=1440)  # 1-day data (1-minute frequency)
    print("✅ Simulation complete.")

import numpy as np
import pandas as pd
import time

def simulate_device_data(device_id, n_samples=1000):
    np.random.seed(42)
    base_temp = np.random.uniform(2, 40)
    base_co = np.random.uniform(0, 20)
    base_co2 = np.random.uniform(200, 1000)
    power = np.random.uniform(100, 2000)

    data = {
        "timestamp": pd.date_range("2025-01-01", periods=n_samples, freq="min"),
        "temperature": base_temp + np.random.randn(n_samples),
        "co": base_co + np.random.randn(n_samples) * 0.5,
        "co2": base_co2 + np.random.randn(n_samples) * 10,
        "power": power + np.random.randn(n_samples) * 5,
    }

    df = pd.DataFrame(data)
    df["device_id"] = device_id
    return df

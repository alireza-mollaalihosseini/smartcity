import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_device_data(device_name, start_time, num_samples=1000, freq_seconds=10):
    timestamps = [start_time + timedelta(seconds=i * freq_seconds) for i in range(num_samples)]
    
    if device_name == "refrigerator":
        temp = np.random.normal(4, 0.5, num_samples)
        co = np.random.normal(2, 0.2, num_samples)
        co2 = np.random.normal(400, 20, num_samples)
        power = np.random.normal(120, 5, num_samples)
    
    elif device_name == "oven":
        temp = np.random.normal(180, 10, num_samples)
        co = np.random.normal(10, 1, num_samples)
        co2 = np.random.normal(600, 30, num_samples)
        power = np.random.normal(2000, 50, num_samples)
    
    elif device_name == "microwave":
        temp = np.random.normal(90, 5, num_samples)
        co = np.random.normal(5, 0.5, num_samples)
        co2 = np.random.normal(450, 25, num_samples)
        power = np.random.normal(800, 20, num_samples)
    
    else:
        raise ValueError("Unknown device name")

    df = pd.DataFrame({
        "timestamp": timestamps,
        "temperature_C": temp,
        "CO_ppm": co,
        "CO2_ppm": co2,
        "power_W": power
    })
    
    return df


def simulate_all_devices(output_dir="simulated_data"):
    os.makedirs(output_dir, exist_ok=True)
    start_time = datetime.now()

    devices = ["refrigerator", "oven", "microwave"]

    for device in devices:
        df = generate_device_data(device, start_time)
        path = os.path.join(output_dir, f"{device}.csv")
        df.to_csv(path, index=False)
        # print(f"✅ Saved simulated data for {device} -> {path}")
        print(f"Saved simulated data for {device} -> {path}")


if __name__ == "__main__":
    simulate_all_devices()

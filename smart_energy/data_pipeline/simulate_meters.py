# smart_energy/data_pipeline/simulate_meters.py
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import argparse

np.random.seed(42)

METER_TYPES = {
    "residential": {"base_kwh": 0.3, "std": 0.1},
    "commercial": {"base_kwh": 2.0, "std": 0.8},
    "industrial": {"base_kwh": 10.0, "std": 3.0}
}

def generate_meter_series(meter_id, meter_type, start, n_samples, freq_minutes=5):
    timestamps = [start + timedelta(minutes=i*freq_minutes) for i in range(n_samples)]
    cfg = METER_TYPES[meter_type]
    base = cfg["base_kwh"]
    noise = cfg["std"]

    # Simulate diurnal pattern (sine) + random noise + occasional spikes
    hours = np.array([ts.hour + ts.minute/60.0 for ts in timestamps])
    diurnal = 1 + 0.5 * np.sin((hours - 6) / 24 * 2 * np.pi)  # peak around evening
    values = base * diurnal + np.random.normal(0, noise, n_samples)

    # occasional anomalies
    n_anom = max(1, int(0.005 * n_samples))
    anom_indices = np.random.choice(n_samples, n_anom, replace=False)
    for idx in anom_indices:
        if np.random.rand() < 0.6:
            values[idx] *= (1 + np.random.uniform(2.0, 6.0))  # spike
        else:
            values[idx] *= np.random.uniform(0.0, 0.2)  # drop / outage

    df = pd.DataFrame({
        "timestamp": timestamps,
        "meter_id": meter_id,
        "meter_type": meter_type,
        "consumption_kwh": values,
        "voltage": 230 + np.random.normal(0, 2, n_samples),
        "frequency_hz": 50 + np.random.normal(0, 0.05, n_samples)
    })
    return df

def generate_weather_series(start, n_samples, freq_minutes=5):
    timestamps = [start + timedelta(minutes=i*freq_minutes) for i in range(n_samples)]
    # basic temp + wind
    temp = 15 + 10 * np.sin(np.linspace(0, 2*np.pi, n_samples)) + np.random.normal(0, 1, n_samples)
    wind = 3 + np.abs(np.random.normal(2, 1, n_samples))
    df = pd.DataFrame({"timestamp": timestamps, "temp_C": temp, "wind_m_s": wind})
    return df

def simulate_many_meters(output_dir="smart_energy/data_pipeline/simulated_energy", n_meters=200, days=1, freq_minutes=5):
    os.makedirs(output_dir, exist_ok=True)
    start = datetime.now() - timedelta(days=days)
    n_samples = int((24*60 / freq_minutes) * days)

    # assign meters
    meter_ids = [f"meter_{i:04d}" for i in range(n_meters)]
    types = np.random.choice(list(METER_TYPES.keys()), size=n_meters, p=[0.7, 0.2, 0.1])

    all_dfs = []
    for m_id, m_type in zip(meter_ids, types):
        df = generate_meter_series(m_id, m_type, start, n_samples, freq_minutes)
        all_dfs.append(df)

    combined = pd.concat(all_dfs, ignore_index=True)
    weather = generate_weather_series(start, n_samples, freq_minutes)
    # Save
    combined.to_csv(os.path.join(output_dir, "meters.csv"), index=False)
    weather.to_csv(os.path.join(output_dir, "weather.csv"), index=False)
    meta = {"n_meters": n_meters, "days": days, "freq_minutes": freq_minutes}
    with open(os.path.join(output_dir, "meta.json"), "w") as f:
        json.dump(meta, f)
    print(f"Saved meters.csv and weather.csv to {output_dir}")

if __name__ == "__main__":
    simulate_many_meters()

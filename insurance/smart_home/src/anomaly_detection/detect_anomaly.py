# detect_anomaly.py (Modified for Smart Home Property Insurance Demo)

import pandas as pd
import json
from sklearn.ensemble import IsolationForest

def detect_anomalies(df):
    """
    Detects anomalies in smart home sensor data.
    Assumes df has columns: 'timestamp', 'device', 'readings' (JSON string).
    Parses readings and uses numeric features for Isolation Forest.
    """
    # Parse JSON readings into separate columns for numeric features
    parsed_data = []
    for _, row in df.iterrows():
        readings = json.loads(row['readings'])
        parsed_row = {
            'timestamp': row['timestamp'],
            'device': row['device'],
            'tenant_id': row.get('tenant_id', 'demo')
        }
        # Flatten relevant numeric readings (handle missing keys gracefully)
        for key, value in readings.items():
            if isinstance(value, (int, float)) and key in ['temp_C', 'humidity_percent', 'smoke_ppm', 'moisture_percent']:
                parsed_row[key] = value
        parsed_data.append(parsed_row)
    
    parsed_df = pd.DataFrame(parsed_data)
    
    # Select available numeric features for anomaly detection
    numeric_features = ['temp_C', 'humidity_percent', 'smoke_ppm', 'moisture_percent']
    available_features = [f for f in numeric_features if f in parsed_df.columns]
    
    if len(available_features) == 0:
        print("⚠️ No numeric features available for anomaly detection.")
        parsed_df["anomaly"] = 1  # No anomaly
        return parsed_df[parsed_df["anomaly"] == -1]  # Empty
    
    features = parsed_df[available_features].fillna(parsed_df[available_features].mean())  # Impute missing
    model = IsolationForest(contamination=0.05, random_state=42)
    parsed_df["anomaly"] = model.fit_predict(features)
    anomalies = parsed_df[parsed_df["anomaly"] == -1]
    return anomalies
# train_predictor.py (Modified for Smart Home Property Insurance Demo)

import pandas as pd
import numpy as np
import json
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

def prepare_features_and_labels(df):
    """
    Prepares X and y from smart home df.
    Assumes df has 'readings' JSON; creates features from numerics.
    y is synthetic 'high_risk' label based on thresholds (e.g., for demo: high temp/smoke/moisture = risk).
    """
    # Parse JSON readings
    parsed_data = []
    for _, row in df.iterrows():
        readings = json.loads(row['readings'])
        parsed_row = {
            'device': row['device'],
            'tenant_id': row.get('tenant_id', 'demo')
        }
        # Flatten numeric features
        for key, value in readings.items():
            if isinstance(value, (int, float)) and key in ['temp_C', 'humidity_percent', 'smoke_ppm', 'moisture_percent']:
                parsed_row[key] = value
        # Synthetic label: high risk if any extreme value (demo purposes)
        risk = 1 if (
            parsed_row.get('temp_C', 0) > 30 or
            parsed_row.get('temp_C', 0) < 10 or
            parsed_row.get('humidity_percent', 0) > 70 or
            parsed_row.get('smoke_ppm', 0) > 20 or
            parsed_row.get('moisture_percent', 0) > 30
        ) else 0
        parsed_row['high_risk'] = risk
        parsed_data.append(parsed_row)
    
    parsed_df = pd.DataFrame(parsed_data)
    
    # Select features
    feature_cols = ['temp_C', 'humidity_percent', 'smoke_ppm', 'moisture_percent']
    available_features = [f for f in feature_cols if f in parsed_df.columns]
    X = parsed_df[available_features].fillna(parsed_df[available_features].mean())
    y = parsed_df['high_risk']
    
    return X, y

def train_predictive_model(X, y=None):
    """
    Trains a Logistic Regression model for risk prediction.
    If y is None, uses prepare_features_and_labels assuming X is a df with 'readings'.
    Predicts binary 'high_risk' for insurance demo (e.g., potential claim trigger).
    """
    if y is None:
        # Assume X is the full df from DB
        X, y = prepare_features_and_labels(X)
    
    # Split for demo evaluation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LogisticRegression(random_state=42)
    model.fit(X_train, y_train)
    
    # Demo accuracy
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"✅ Model trained with accuracy: {accuracy:.2f} on test set.")
    
    return model
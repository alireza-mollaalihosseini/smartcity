import os
import subprocess
import time
import sys
import signal
import sqlite3
from functools import wraps

import pandas as pd
from flask import Flask, jsonify, request
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

import jwt
import datetime

# ========================= CONFIG =========================
SECRET_KEY = os.getenv("JWT_SECRET", "fallback-CHANGE-THIS-IMMEDIATELY-TO-A-STRONG-SECRET")
DB_PATH = os.getenv("DB_PATH", "smart_home.db")
MODELS_PATH = os.getenv("MODELS_PATH", "models")
ALERTS_PATH = os.getenv("ALERTS_PATH", "alerts")
TENANT_ID = os.getenv("TENANT_ID", "demo")

# Simple in-memory users (replace with real DB later)
USERS = {
    "demo@customer.com": "demo123",
    "customer1@company.com": "pass123"
}

app = Flask(__name__)

# ========================= JWT AUTH DECORATOR =========================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token is missing or invalid"}), 401

        token = auth_header.split(" ")[1]

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated


# ========================= ROUTES =========================
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "service": "smart-home-insurance-demo",
        "tenant_id": TENANT_ID
    })

@app.route('/login', methods=['POST'])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    if USERS.get(email) == password:
        token = jwt.encode({
            'email': email,
            'tenant_id': email.split('@')[0],  # e.g. "demo" or "customer1"
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')

        return jsonify({
            "token": token,
            "tenant_id": email.split('@')[0],
            "message": "Login successful"
        })

    return jsonify({"error": "Invalid credentials"}), 401


@app.route('/devices')
@token_required
def api_devices():
    tenant_id = request.current_user['tenant_id']
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT DISTINCT device FROM sensor_data WHERE tenant_id = ?"
    df = pd.read_sql(query, conn, params=(tenant_id,))
    conn.close()
    return jsonify(df['device'].tolist())


@app.route('/live-data/<device>')
@token_required
def api_live_data(device):
    tenant_id = request.current_user['tenant_id']
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT timestamp, device, readings
        FROM sensor_data 
        WHERE tenant_id = ? AND device = ? 
        ORDER BY timestamp DESC LIMIT 100
    """
    df = pd.read_sql(query, conn, params=(tenant_id, device))
    conn.close()
    # Return oldest first for charts; readings is JSON string, frontend can parse
    return jsonify(df[::-1].to_dict(orient='records'))


@app.route('/predictions')
@token_required
def api_predictions():
    tenant_id = request.current_user['tenant_id']
    pred_file = os.path.join(MODELS_PATH, f"predictions_{tenant_id}.csv")
    
    if not os.path.exists(pred_file):
        return jsonify({"error": "Predictions not ready yet"}), 404
    
    df = pd.read_csv(pred_file)
    return jsonify(df.to_dict(orient='records'))


@app.route('/alerts')
@token_required
def api_alerts():
    tenant_id = request.current_user['tenant_id']
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT timestamp, device, message, severity
        FROM alerts 
        WHERE tenant_id = ? 
        ORDER BY timestamp DESC LIMIT 20
    """
    df = pd.read_sql(query, conn, params=(tenant_id,))
    conn.close()
    alerts = df.to_dict(orient='records')
    return jsonify(alerts)


# ========================= BACKGROUND SERVICES =========================
def run_script(script_path, description=None):
    cmd = [sys.executable, script_path]
    desc = description or os.path.basename(script_path)
    print(f"Running: {desc}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error in {desc}:\n{result.stderr}")
        sys.exit(1)
    else:
        print(f"{desc} completed.")
        if result.stdout.strip():
            print(result.stdout)


def signal_handler(signum, frame):
    print("\nShutting down gracefully...")
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    print("\n===============================")
    print("SMART HOME INSURANCE DEMO STARTED")
    print("===============================\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Paths (adjusted for insurance project files)
    simulate_path = os.path.join(base_dir, "data_pipeline", "data.py")
    ingestion_path = os.path.join(base_dir, "data_pipeline", "data_ingestion.py")
    anomaly_model_path = os.path.join(base_dir, "src", "anomaly_detection", "detect_anomaly.py")
    predictive_model_path = os.path.join(base_dir, "src", "predictive_maintenance", "train_predictor.py")
    alert_system_path = os.path.join(base_dir, "alerts", "alert_system.py")

    # Environment for child processes
    mqtt_env = os.environ.copy()

    # Background processes dict
    backgrounds = {}

    try:
        # 1. Start simulation
        sim_log = os.path.join(ALERTS_PATH, 'simulation.log')
        backgrounds['simulation'] = subprocess.Popen(
            [sys.executable, simulate_path, "--duration=indefinite"],
            env=mqtt_env,
            stdout=open(sim_log, 'w'),
            stderr=subprocess.STDOUT
        )
        print(f"Simulation started → {sim_log}")

        # 2. Start ingestion
        ingest_log = os.path.join(ALERTS_PATH, 'ingestion.log')
        backgrounds['ingestion'] = subprocess.Popen(
            [sys.executable, ingestion_path],
            env=mqtt_env,
            stdout=open(ingest_log, 'w'),
            stderr=subprocess.STDOUT
        )
        print(f"Ingestion started → {ingest_log}")

        # Wait for initial data
        print("Waiting 30s for initial data...")
        time.sleep(30)

        # 3. Train models (foreground)
        run_script(anomaly_model_path, "Running anomaly detection")
        run_script(predictive_model_path, "Training risk prediction model")

        # 4. Start alert system
        alert_log = os.path.join(ALERTS_PATH, 'alerts.log')
        backgrounds['alerts'] = subprocess.Popen(
            [sys.executable, alert_system_path],
            env=mqtt_env,
            stdout=open(alert_log, 'w'),
            stderr=subprocess.STDOUT
        )
        print(f"Alert system started → {alert_log}")

        print("\nAll background services running.")
        print("Health: http://localhost:8080/health")
        print("API:    http://localhost:8080/api/...\n")

        # Start Flask API (blocking)
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        print("Terminating background processes...")
        for name, proc in backgrounds.items():
            if proc.poll() is None:
                print(f"Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()
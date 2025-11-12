import os
import subprocess
import time
import sys
import signal
from flask import Flask, jsonify

def run_script(script_path, description=None, background=False):
    """Run a Python script (foreground or background)."""
    cmd = [sys.executable, script_path]
    if description:
        desc = f"{description} — Running: {os.path.basename(script_path)}"
    else:
        desc = f"Running: {os.path.basename(script_path)}"
    
    if background:
        # For long-running services (direct Popen for parallelism)
        print(f"\n🚀 {desc} — Starting background: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc
    else:
        # Foreground (your original logic)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ {os.path.basename(script_path)} completed successfully.\n")
            if result.stdout.strip():
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error while running {os.path.basename(script_path)}:\n{e.stderr}")
            sys.exit(1)

def signal_handler(signum, frame):
    """Graceful shutdown on Ctrl+C."""
    print("\n🛑 Shutting down Smart Kitchen...")
    sys.exit(0)

# Flask health app (for AWS/ECS health checks)
app_health = Flask(__name__)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n==============================")
    print("🤖 SMART KITCHEN AUTOMATION STARTED (AWS IoT Core Mode)")
    print("==============================\n")

    # Get base dir (full path for reliability in Docker/AWS)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Env vars (DB, models, alerts; IoT Core MQTT)
    db_path = os.getenv('DB_PATH', os.path.join(base_dir, 'kitchen.db'))
    models_path = os.getenv('MODELS_PATH', os.path.join(base_dir, 'models'))
    alerts_path = os.getenv('ALERTS_PATH', os.path.join(base_dir, 'alerts'))

    # IoT Core env vars (passed to subprocesses; fallback to local MQTT for dev)
    mqtt_env = os.environ.copy()
    mqtt_env.update({
        'MQTT_ENDPOINT': os.getenv('MQTT_ENDPOINT', 'localhost'),
        'MQTT_PORT': str(os.getenv('MQTT_PORT', 8883 if os.getenv('MQTT_ENDPOINT') != 'localhost' else 1883)),
        'CA_PATH': os.getenv('CA_PATH', ''),
        'CERT_PATH': os.getenv('CERT_PATH', ''),
        'KEY_PATH': os.getenv('KEY_PATH', ''),
        'DB_PATH': db_path,
        'MODELS_PATH': models_path,
        'ALERTS_PATH': alerts_path
    })

    # === Define all important paths ===
    simulate_path = os.path.join(base_dir, "data_pipeline", "data_iot.py")
    ingestion_path = os.path.join(base_dir, "data_pipeline", "data_ingestion_iot.py")
    anomaly_model_path = os.path.join(base_dir, "src", "anomaly_detection", "detect_anomaly.py")
    predictive_model_path = os.path.join(base_dir, "src", "predictive_maintenance", "train_predictor.py")
    alert_system_path = os.path.join(base_dir, "alerts", "alert_system_iot.py")

    # Background services dict (for management)
    backgrounds = {}

    try:
        # Step 1: Start simulation (background)
        backgrounds['simulation'] = subprocess.Popen(
            [sys.executable, simulate_path, "--duration=indefinite"],
            env=mqtt_env,  # Pass all envs
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Simulation started in background.")

        # Step 2: Start ingestion (background)
        backgrounds['ingestion'] = subprocess.Popen(
            [sys.executable, ingestion_path],
            env=mqtt_env,  # Pass all envs
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Ingestion started in background.")

        # Warm-up
        print("\n⏳ Warm-up: Waiting 30s for initial data...")
        time.sleep(30)

        # Steps 3-4: Train models (foreground, unchanged)
        run_script(anomaly_model_path, "Step 3: Training anomaly detection model")
        run_script(predictive_model_path, "Step 4: Training predictive maintenance model")

        # Step 5: Start alerts (background)
        backgrounds['alerts'] = subprocess.Popen(
            [sys.executable, alert_system_path],
            env=mqtt_env,  # Pass all envs
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Alerts started in background.")

        # Dashboard runs in separate Docker service; run health server
        print("\n📊 Dashboard available at http://localhost:8501 (separate service)\n")
        print("🔄 Health endpoint at http://localhost:8080/health | Keeping services running...")

        # Health endpoint
        @app_health.route('/health')
        def health():
            active_services = len([p for p in backgrounds.values() if p.poll() is None])
            return jsonify({
                'status': 'healthy' if active_services >= 3 else 'unhealthy',
                'active_services': active_services,
                'total_backgrounds': len(backgrounds)
            })

        # Run Flask (blocks gracefully)
        app_health.run(host='0.0.0.0', port=8080, debug=False)

    except KeyboardInterrupt:
        print("\n🛑 Interrupt received.")
    finally:
        for name, proc in backgrounds.items():
            if proc.poll() is None:
                print(f"🛑 Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()
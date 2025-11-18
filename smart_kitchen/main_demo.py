import os
import subprocess
import time
import sys
import signal
from flask import Flask, jsonify
from dotenv import load_dotenv
load_dotenv()  # Load .env for this script and subprocesses

def run_script(script_path, description=None, background=False):
    cmd = [sys.executable, script_path]
    if description:
        desc = f"{description} — Running: {os.path.basename(script_path)}"
    else:
        desc = f"Running: {os.path.basename(script_path)}"
    
    if background:
        print(f"\n🚀 {desc} — Starting background: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc
    else:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ {os.path.basename(script_path)} completed successfully.\n")
            if result.stdout.strip():
                print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error while running {os.path.basename(script_path)}:\n{e.stderr}")
            sys.exit(1)

def signal_handler(signum, frame):
    print("\n🛑 Shutting down...")
    sys.exit(0)

app_health = Flask(__name__)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n==============================")
    print("🤖 SMART KITCHEN AUTOMATION STARTED (AWS IoT Core Mode)")
    print("==============================\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    db_path = os.getenv('DB_PATH', os.path.join(base_dir, 'kitchen.db'))
    models_path = os.getenv('MODELS_PATH', os.path.join(base_dir, 'models'))
    alerts_path = os.getenv('ALERTS_PATH', os.path.join(base_dir, 'alerts'))
    tenant_id = os.getenv('TENANT_ID', 'demo')

    mqtt_env = os.environ.copy()
    # Debug print env
    print(f"🔍 App env: MQTT_ENDPOINT={os.getenv('MQTT_ENDPOINT')}, TENANT_ID={tenant_id}")
    mqtt_env.update({
        'MQTT_ENDPOINT': os.getenv('MQTT_ENDPOINT', 'localhost'),
        'MQTT_PORT': str(os.getenv('MQTT_PORT', 8883 if os.getenv('MQTT_ENDPOINT') != 'localhost' else 1883)),
        'CA_PATH': os.getenv('CA_PATH', ''),
        'CERT_PATH': os.getenv('CERT_PATH', ''),
        'KEY_PATH': os.getenv('KEY_PATH', ''),
        'DB_PATH': db_path,
        'MODELS_PATH': models_path,
        'ALERTS_PATH': alerts_path,
        'TENANT_ID': tenant_id
    })

    # Paths (demo naming)
    simulate_path = os.path.join(base_dir, "data_pipeline", "data_demo.py")
    ingestion_path = os.path.join(base_dir, "data_pipeline", "data_ingestion_demo.py")
    anomaly_model_path = os.path.join(base_dir, "src", "anomaly_detection", "detect_anomaly.py")
    predictive_model_path = os.path.join(base_dir, "src", "predictive_maintenance", "train_predictor.py")
    alert_system_path = os.path.join(base_dir, "alerts", "alert_system_demo.py")

    # backgrounds = {}

    # try:
    #     # Simulation (background)
    #     backgrounds['simulation'] = subprocess.Popen(
    #         [sys.executable, simulate_path, "--duration=indefinite"],
    #         env=mqtt_env,
    #         stdout=subprocess.PIPE, stderr=subprocess.PIPE
    #     )
    #     print(f"✅ Simulation started for tenant {tenant_id}.")

    #     # Ingestion (background)
    #     backgrounds['ingestion'] = subprocess.Popen(
    #         [sys.executable, ingestion_path],
    #         env=mqtt_env,
    #         stdout=subprocess.PIPE, stderr=subprocess.PIPE
    #     )
    #     print(f"✅ Ingestion started for tenant {tenant_id}.")

    #     # Warm-up
    #     print(f"\n⏳ Waiting 30s for initial data (Tenant: {tenant_id})...")
    #     time.sleep(30)

    #     # Models (foreground)
    #     run_script(anomaly_model_path, "Training anomaly detection model")
    #     run_script(predictive_model_path, "Training predictive maintenance model")

    #     # Alerts (background)
    #     backgrounds['alerts'] = subprocess.Popen(
    #         [sys.executable, alert_system_path],
    #         env=mqtt_env,
    #         stdout=subprocess.PIPE, stderr=subprocess.PIPE
    #     )
    #     print(f"✅ Alerts started for tenant {tenant_id}.")

    # Background services dict
    backgrounds = {}

    try:
        # Step 1: Start simulation (background, log to file)
        sim_log = os.path.join(alerts_path, 'simulation.log')
        backgrounds['simulation'] = subprocess.Popen(
            [sys.executable, simulate_path, "--duration=indefinite"],
            env=mqtt_env,
            stdout=open(sim_log, 'w'),  # Log to file
            stderr=subprocess.STDOUT  # Merge stderr to stdout
        )
        print(f"✅ Simulation started for tenant {tenant_id}. Logs: {sim_log}")

        # Step 2: Start ingestion (background, log to file)
        ingest_log = os.path.join(alerts_path, 'ingestion.log')
        backgrounds['ingestion'] = subprocess.Popen(
            [sys.executable, ingestion_path],
            env=mqtt_env,
            stdout=open(ingest_log, 'w'),
            stderr=subprocess.STDOUT
        )
        print(f"✅ Ingestion started for tenant {tenant_id}. Logs: {ingest_log}")

        # Warm-up
        print(f"\n⏳ Waiting 30s for initial data (Tenant: {tenant_id})...")
        time.sleep(30)

        # Models (foreground)
        run_script(anomaly_model_path, "Training anomaly detection model")
        run_script(predictive_model_path, "Training predictive maintenance model")

        # Step 5: Start alerts (background, log to file)
        alert_log = os.path.join(alerts_path, 'alerts.log')
        backgrounds['alerts'] = subprocess.Popen(
            [sys.executable, alert_system_path],
            env=mqtt_env,
            stdout=open(alert_log, 'w'),
            stderr=subprocess.STDOUT
        )
        print(f"✅ Alerts started for tenant {tenant_id}. Logs: {alert_log}")

        print(f"\n📊 Dashboard at http://localhost (separate service; Tenant: {tenant_id})\n")
        print("🔄 Health at http://localhost:8080/health | Keeping running...")

        @app_health.route('/health')
        def health():
            active = len([p for p in backgrounds.values() if p.poll() is None])
            return jsonify({
                'status': 'healthy' if active >= 3 else 'unhealthy',
                'active_services': active,
                'total_backgrounds': len(backgrounds),
                'tenant_id': tenant_id
            })

        app_health.run(host='0.0.0.0', port=8080, debug=False)

    except KeyboardInterrupt:
        print(f"\n🛑 Interrupt for tenant {tenant_id}.")
    finally:
        for name, proc in backgrounds.items():
            if proc.poll() is None:
                print(f"🛑 Stopping {name}...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print("✅ All stopped.")

if __name__ == "__main__":
    main()
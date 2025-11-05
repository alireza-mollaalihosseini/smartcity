import os
import subprocess
import time
import sys
import signal
from contextlib import contextmanager

@contextmanager
def background_process(cmd, description):
    """Run a subprocess in background and yield its Popen obj."""
    print(f"\n🚀 {description} — Starting background: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        yield proc
    finally:
        print(f"🛑 Stopping {description}...")
        proc.terminate()
        proc.wait(timeout=10)  # Graceful stop

def run_script(script_path, description=None, background=False):
    """Run a Python script (foreground or background)."""
    cmd = [sys.executable, script_path]
    if description:
        desc = f"{description} — Running: {os.path.basename(script_path)}"
    else:
        desc = f"Running: {os.path.basename(script_path)}"
    
    if background:
        # For long-running services
        with background_process(cmd, desc):
            # This context will run the process during the 'with' block
            # But for parallel, we'll use multiple in main()
            pass  # Actual usage in main()
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

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\n==============================")
    print("🤖 SMART KITCHEN AUTOMATION STARTED (Kafka Streaming Mode)")
    print("==============================\n")

    base_dir = os.path.dirname(__file__)
    os.path.join()

    # === Define all important paths ===
    simulate_path = os.path.join(base_dir, '..', "data_pipeline", "data_mqtt.py")
    ingestion_path = os.path.join(base_dir, '..', "data_pipeline", "data_ingestion_mqtt.py")
    anomaly_model_path = os.path.join(base_dir, '..', "src", "anomaly_detection", "detect_anomaly.py")
    predictive_model_path = os.path.join(base_dir, '..', "src", "predictive_maintenance", "train_predictor.py")
    alert_system_path = os.path.join(base_dir, '..', "alerts", "alert_system_mqtt.py")
    dashboard_path = os.path.join(base_dir, '..', "dashboard", "dashboard_app_mqtt.py")

    # Background services dict (for management)
    backgrounds = {}

    try:
        # Step 1: Start simulation (background)
        backgrounds['simulation'] = subprocess.Popen(
            [sys.executable, simulate_path, "--duration=indefinite"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Simulation started in background.")

        # Step 2: Start ingestion (background)
        backgrounds['ingestion'] = subprocess.Popen(
            [sys.executable, ingestion_path],
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
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print("✅ Alerts started in background.")

        # Step 6: Dashboard (unchanged)
        print("\n📊 Step 6: Starting dashboard (press Ctrl + C to stop)...\n")
        time.sleep(2)
        subprocess.run(
            ["streamlit", "run", dashboard_path],
            cwd=os.path.dirname(dashboard_path),
            check=True
        )

    except KeyboardInterrupt:
        print("\n🛑 Interrupt received.")
    finally:
        for name, proc in backgrounds.items():
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()
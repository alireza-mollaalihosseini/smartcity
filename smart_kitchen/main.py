# import os
# import subprocess
# import time

# def run_script(script_path):
#     """Run a Python script and wait for completion."""
#     print(f"\n🚀 Running: {script_path}")
#     result = subprocess.run(["python", script_path], capture_output=True, text=True)
#     if result.returncode == 0:
#         print(f"✅ {script_path} completed successfully.\n")
#         print(result.stdout)
#     else:
#         print(f"❌ Error in {script_path}:\n{result.stderr}")

# def main():
#     print("\n==============================")
#     print("SMART KITCHEN AUTOMATION STARTED")
#     print("==============================\n")
#     base_dir = os.path.dirname(os.path.abspath(__file__))

#     # Step 1: Simulate sensor data
#     run_script(os.path.join(base_dir, "../smart_kitchen/simulate_sensors.py"))

#     # Step 2: Store simulated data locally (SQLite)
#     run_script(os.path.join(base_dir, "../smart_kitchen/data_pipeline/store_data.py"))

#     # Step 3: Train ML model for anomaly detection
#     run_script(os.path.join(base_dir, "../smart_kitchen/model/train_model.py"))

#     # Step 4: Visualize results (if available)
#     print("\n📊 Starting dashboard (press Ctrl+C to stop)...\n")
#     time.sleep(2)
#     subprocess.run(["python", "smart_kitchen/dashboard/dashboard.py"])

# if __name__ == "__main__":
#     main()


import os
import subprocess
import time
import sys


def run_script(script_path, description=None):
    """Run a Python script and handle success or errors gracefully."""
    if description:
        print(f"\n🚀 {description} — Running: {os.path.basename(script_path)}")
    else:
        print(f"\n🚀 Running: {os.path.basename(script_path)}")

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {os.path.basename(script_path)} completed successfully.\n")
        if result.stdout.strip():
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error while running {os.path.basename(script_path)}:\n{e.stderr}")
        sys.exit(1)


def main():
    print("\n==============================")
    print("🤖 SMART KITCHEN AUTOMATION STARTED")
    print("==============================\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    # smart_kitchen_dir = os.path.join(base_dir, "smart_kitchen")

    # === Define all important paths ===
    simulate_path = os.path.join(base_dir, "data_pipeline", "data_simulation.py")
    ingestion_path = os.path.join(base_dir, "data_pipeline", "data_ingestion.py")
    anomaly_model_path = os.path.join(base_dir, "src", "anomaly_detection", "detect_anomaly.py")
    predictive_model_path = os.path.join(base_dir, "src", "predictive_maintenance", "train_predictor.py")
    alert_system_path = os.path.join(base_dir, "alerts", "alert_system.py")
    dashboard_path = os.path.join(base_dir, "dashboard", "dashboard_app.py")

    # === Step 1: Simulate sensor data ===
    run_script(simulate_path, "Step 1: Simulating sensor data")

    # === Step 2: Store simulated data locally (SQLite) ===
    run_script(ingestion_path, "Step 2: Storing simulated data to database")

    # === Step 3: Train anomaly detection model ===
    run_script(anomaly_model_path, "Step 3: Training anomaly detection model")

    # === Step 4: Train predictive maintenance model ===
    run_script(predictive_model_path, "Step 4: Training predictive maintenance model")

    # === Step 5: Run alert system ===
    run_script(alert_system_path, "Step 5: Checking and sending alerts")

    # === Step 6: Start the dashboard ===
    print("\n📊 Step 6: Starting dashboard (press Ctrl + C to stop)...\n")
    time.sleep(2)

    # Use 'streamlit run' to properly launch the app
    try:
        subprocess.run(
            ["streamlit", "run", dashboard_path],
            cwd=os.path.dirname(dashboard_path),
            check=True
        )
    except FileNotFoundError:
        print("Error: 'streamlit' command not found. Ensure Streamlit is installed: pip install streamlit")
    except subprocess.CalledProcessError as e:
        print(f"Dashboard failed to start: {e}")
    except KeyboardInterrupt:
        print("\nDashboard stopped by user.")

if __name__ == "__main__":
    main()

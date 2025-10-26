import os
import pandas as pd
import joblib
import sqlite3
import smtplib
from email.mime.text import MIMEText

# === CONFIGURATION ===
base_dir = os.path.dirname(os.path.abspath(__file__))
TEMP_THRESHOLD = 10  # degrees above normal mean
ALERT_LOG_PATH = os.path.join(base_dir, "../alerts/alert_log.txt") # "alerts/alert_log.txt"
DB_PATH = os.path.join(base_dir, "../data_pipeline/smart_kitchen.db") # "data_pipeline/smart_kitchen.db"
MODEL_PATH = os.path.join(base_dir, "../models/saved_models/predictive_maintenance.pkl") # "models/saved_models/predictive_maintenance.pkl"
ANOMALY_RESULTS = os.path.join(base_dir, "../models/results/anomaly_results.csv") # "models/results/anomaly_results.csv"

# === BASIC ALERT FUNCTION ===
def send_local_alert(device, message):
    os.makedirs(os.path.dirname(ALERT_LOG_PATH), exist_ok=True)
    with open(ALERT_LOG_PATH, "a") as log:
        log.write(f"[ALERT] {device}: {message}\n")
    # print(f"🚨 ALERT for {device}: {message}")
    print(f"ALERT for {device}: {message}")


# === OPTIONAL EMAIL FUNCTION (for future AWS SNS or SMTP setup) ===
def send_email_alert(to_email, subject, message):
    sender = "noreply@smartkitchen.io"
    msg = MIMEText(message)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    # Uncomment this block if you have an SMTP server
    # with smtplib.SMTP("smtp.gmail.com", 587) as server:
    #     server.starttls()
    #     server.login(sender, "YOUR_APP_PASSWORD")
    #     server.send_message(msg)
    # print(f"📧 Email sent to {to_email}")

# === CHECK FOR ANOMALIES ===
def check_anomalies():
    if not os.path.exists(ANOMALY_RESULTS):
        # print("⚠️ No anomaly results found.")
        print("No anomaly results found.")
        return
    df = pd.read_csv(ANOMALY_RESULTS)
    for device in df["device"].unique():
        device_df = df[df["device"] == device]
        anomaly_rate = device_df["anomaly"].mean()
        if anomaly_rate > 0.05:
            send_local_alert(device, f"High anomaly rate detected ({anomaly_rate:.1%})")


# === CHECK PREDICTIVE MAINTENANCE ===
# def check_predictions():
#     if not os.path.exists(MODEL_PATH):
#         print("⚠️ Predictive maintenance model not found.")
#         return

#     # Load latest data
#     conn = sqlite3.connect(DB_PATH)
#     df = pd.read_sql("SELECT * FROM sensor_data", conn)
#     conn.close()
#     df["timestamp"] = pd.to_datetime(df["timestamp"])
#     df = df.sort_values(by=["device", "timestamp"])

#     model = joblib.load(MODEL_PATH)
#     features = ["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]

#     for device in df["device"].unique():
#         device_df = df[df["device"] == device].tail(10)
#         X = device_df[features].mean().values.reshape(1, -1)
#         future_temp = model.predict(X)[0]
#         avg_temp = device_df["temperature_C"].mean()

#         if future_temp > avg_temp + TEMP_THRESHOLD:
#             send_local_alert(device, f"Predicted overheating: {future_temp:.1f}°C")
def check_predictions():
    """Check predictive maintenance based on latest sensor readings and trained model."""
    if not os.path.exists(MODEL_PATH):
        # print("⚠️ Predictive maintenance model not found.")
        print("Predictive maintenance model not found.")
        return

    # Load model
    model = joblib.load(MODEL_PATH)

    # Load latest sensor data
    if not os.path.exists(DB_PATH):
        # print("⚠️ Database not found.")
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM sensor_data", conn)
    conn.close()

    if df.empty:
        # print("⚠️ No sensor data found in database.")
        print("No sensor data found in database.")
        return

    # === Preprocess data ===
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["device", "timestamp"])

    # Recreate rolling features consistent with training
    window = 5
    df["temperature_C_mean"] = df.groupby("device")["temperature_C"].transform(lambda x: x.rolling(window).mean())
    df["temperature_C_std"] = df.groupby("device")["temperature_C"].transform(lambda x: x.rolling(window).std())
    df["power_mean"] = df.groupby("device")["power_W"].transform(lambda x: x.rolling(window).mean())
    df["CO_mean"] = df.groupby("device")["CO_ppm"].transform(lambda x: x.rolling(window).mean())
    df["CO2_mean"] = df.groupby("device")["CO2_ppm"].transform(lambda x: x.rolling(window).mean())

    df = df.dropna()

    features = [col for col in df.columns if "mean" in col or "std" in col]

    # === Predict for each device ===
    for device in df["device"].unique():
        device_df = df[df["device"] == device].tail(1)  # last available entry
        X = device_df[features]

        future_temp_pred = model.predict(X)[0]
        avg_temp_recent = device_df["temperature_C_mean"].values[0]

        if future_temp_pred > avg_temp_recent + TEMP_THRESHOLD:
            send_local_alert(device, f"Predicted overheating: {future_temp_pred:.1f}°C (avg: {avg_temp_recent:.1f}°C)")
        else:
            # print(f"[✓] {device}: Stable (predicted {future_temp_pred:.1f}°C, avg {avg_temp_recent:.1f}°C)")
            print(f"{device}: Stable (predicted {future_temp_pred:.1f}°C, avg {avg_temp_recent:.1f}°C)")

    # print("✅ Predictive maintenance check completed.")
    print("Predictive maintenance check completed.")


def run_alert_system():
    # print("🔎 Checking anomalies...")
    print("Checking anomalies...")
    check_anomalies()

    # print("🔮 Checking predictive maintenance...")
    print("Checking predictive maintenance...")
    check_predictions()

    # print("✅ Alert system finished checking.")
    print("Alert system finished checking.")


if __name__ == "__main__":
    run_alert_system()

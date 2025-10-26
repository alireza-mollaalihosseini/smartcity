import os
import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

base_dir = os.path.dirname(os.path.abspath(__file__))
ALERT_LOG = os.path.join(base_dir, "../alerts/alert_log.txt") # "alerts/alert_log.txt"
DB_PATH = os.path.join(base_dir, "../data_pipeline/smart_kitchen.db") # "data_pipeline/smart_kitchen.db"
ANOMALY_PATH = os.path.join(base_dir, "../models/results/anomaly_results.csv") # "models/results/anomaly_results.csv"

st.set_page_config(page_title="Smart Kitchen Dashboard", layout="wide")

st.title("🍳 Smart Kitchen Monitoring Dashboard")
st.markdown("Real-time visualization of IoT sensor data, anomalies, and maintenance predictions.")

# === Load Data ===
@st.cache_data
def load_sensor_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM sensor_data", conn)
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

@st.cache_data
def load_anomalies():
    try:
        df = pd.read_csv(ANOMALY_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def load_alerts():
    if not os.path.exists(ALERT_LOG):
        return []
    with open(ALERT_LOG, "r") as f:
        return f.readlines()

# === Display Sections ===
st.sidebar.header("Navigation")
section = st.sidebar.radio("Go to:", ["Sensor Data", "Anomaly Detection", "Alerts"])

data = load_sensor_data()
devices = sorted(data["device"].unique())
selected_device = st.sidebar.selectbox("Select Device", devices)

device_data = data[data["device"] == selected_device]

if section == "Sensor Data":
    st.subheader(f"📈 Sensor Readings — {selected_device}")
    st.line_chart(device_data.set_index("timestamp")[["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]])

    st.markdown("**Summary Statistics**")
    st.dataframe(device_data.describe().round(2))

elif section == "Anomaly Detection":
    anomalies = load_anomalies()
    if anomalies.empty:
        st.warning("No anomaly data available yet.")
    else:
        st.subheader(f"🚨 Anomaly Detection — {selected_device}")
        dev_anom = anomalies[anomalies["device"] == selected_device]
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dev_anom["timestamp"], dev_anom["temperature_C"], label="Temperature")
        ax.scatter(
            dev_anom[dev_anom["anomaly"] == 1]["timestamp"],
            dev_anom[dev_anom["anomaly"] == 1]["temperature_C"],
            color="red", label="Anomaly", zorder=5
        )
        ax.legend()
        ax.set_title(f"Temperature and Anomalies for {selected_device}")
        st.pyplot(fig)

elif section == "Alerts":
    st.subheader("🔔 System Alerts")
    alerts = load_alerts()
    if not alerts:
        st.info("No alerts generated yet.")
    else:
        for line in alerts:
            st.error(line.strip())

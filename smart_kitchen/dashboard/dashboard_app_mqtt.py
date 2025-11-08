# import os
# import sqlite3
# import pandas as pd
# import streamlit as st
# import matplotlib.pyplot as plt

# base_dir = os.path.dirname(os.path.abspath(__file__))
# ALERT_LOG = os.path.join(base_dir, "../alerts/alert_log.txt") # "alerts/alert_log.txt"
# DB_PATH = os.path.join(base_dir, "../data_pipeline/kitchen.db") # "data_pipeline/smart_kitchen.db"
# ANOMALY_PATH = os.path.join(base_dir, "../models/results/anomaly_results.csv") # "models/results/anomaly_results.csv"

# st.set_page_config(page_title="Smart Kitchen Dashboard", layout="wide")

# st.title("🍳 Smart Kitchen Monitoring Dashboard")
# st.markdown("Real-time visualization of IoT sensor data, anomalies, and maintenance predictions.")

# # === Load Data ===
# @st.cache_data
# def load_sensor_data():
#     conn = sqlite3.connect(DB_PATH)
#     df = pd.read_sql("SELECT * FROM sensor_data", conn)
#     conn.close()
#     df["timestamp"] = pd.to_datetime(df["timestamp"])
#     return df

# @st.cache_data
# def load_anomalies():
#     try:
#         df = pd.read_csv(ANOMALY_PATH)
#         df["timestamp"] = pd.to_datetime(df["timestamp"])
#         return df
#     except FileNotFoundError:
#         return pd.DataFrame()

# def load_alerts():
#     if not os.path.exists(ALERT_LOG):
#         return []
#     with open(ALERT_LOG, "r") as f:
#         return f.readlines()

# # === Display Sections ===
# st.sidebar.header("Navigation")
# section = st.sidebar.radio("Go to:", ["Sensor Data", "Anomaly Detection", "Alerts"])

# data = load_sensor_data()
# devices = sorted(data["device"].unique())
# selected_device = st.sidebar.selectbox("Select Device", devices)

# device_data = data[data["device"] == selected_device]

# if section == "Sensor Data":
#     st.subheader(f"📈 Sensor Readings — {selected_device}")
#     st.line_chart(device_data.set_index("timestamp")[["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]])

#     st.markdown("**Summary Statistics**")
#     st.dataframe(device_data.describe().round(2))

# elif section == "Anomaly Detection":
#     anomalies = load_anomalies()
#     if anomalies.empty:
#         st.warning("No anomaly data available yet.")
#     else:
#         st.subheader(f"🚨 Anomaly Detection — {selected_device}")
#         dev_anom = anomalies[anomalies["device"] == selected_device]
#         fig, ax = plt.subplots(figsize=(10, 4))
#         ax.plot(dev_anom["timestamp"], dev_anom["temperature_C"], label="Temperature")
#         ax.scatter(
#             dev_anom[dev_anom["anomaly"] == 1]["timestamp"],
#             dev_anom[dev_anom["anomaly"] == 1]["temperature_C"],
#             color="red", label="Anomaly", zorder=5
#         )
#         ax.legend()
#         ax.set_title(f"Temperature and Anomalies for {selected_device}")
#         st.pyplot(fig)

# elif section == "Alerts":
#     st.subheader("🔔 System Alerts")
#     alerts = load_alerts()
#     if not alerts:
#         st.info("No alerts generated yet.")
#     else:
#         for line in alerts:
#             st.error(line.strip())


# import os
# import sqlite3
# import pandas as pd
# import streamlit as st
# import matplotlib.pyplot as plt
# import json
# import threading
# import time
# from datetime import datetime
# import paho.mqtt.client as mqtt

# base_dir = os.path.dirname(os.path.abspath(__file__))
# ALERT_LOG = os.path.join(base_dir, "../alerts/alert_log.txt")  # Fallback
# # DB_PATH = os.path.join(base_dir, "../kitchen.db")
# DB_PATH = "/app/kitchen.db"
# ANOMALY_PATH = os.path.join(base_dir, "../models/results/anomaly_results.csv")

# # MQTT config
# # MQTT_BROKER = 'localhost'
# MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
# MQTT_PORT = 1883
# MQTT_PREFIX = 'smart_kitchen/'
# ALERT_TOPIC = MQTT_PREFIX + 'alerts'

# st.set_page_config(page_title="Smart Kitchen Dashboard", layout="wide")

# st.title("🍳 Smart Kitchen Monitoring Dashboard (MQTT Live Mode)")
# st.markdown("Real-time IoT sensor streaming, anomalies, and instant alerts via MQTT.")

# # === Global Setup ===
# if 'live_sensor_data' not in st.session_state:
#     # Initialize with historical DB data
#     conn = sqlite3.connect(DB_PATH)
#     df = pd.read_sql("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 500", conn)  # Last 500 for perf
#     conn.close()
#     df["timestamp"] = pd.to_datetime(df["timestamp"])
#     st.session_state.live_sensor_data = df.sort_values('timestamp')

# if 'live_alerts' not in st.session_state:
#     st.session_state.live_alerts = []

# if 'mqtt_client' not in st.session_state:
#     st.session_state.mqtt_client = None
#     st.session_state.mqtt_thread = None

# # === MQTT Live Updater ===
# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         st.session_state.mqtt_connected = True
#         print("✅ MQTT connected for dashboard.")
#         devices = ["refrigerator", "oven", "microwave"]
#         for device in devices:
#             topic = MQTT_PREFIX + device
#             client.subscribe(topic)
#         client.subscribe(ALERT_TOPIC)
#     else:
#         st.session_state.mqtt_connected = False
#         print(f"❌ MQTT connect failed: {rc}")

# def on_message(client, userdata, msg):
#     try:
#         if msg.topic == ALERT_TOPIC:
#             alert = json.loads(msg.payload.decode())
#             st.session_state.live_alerts.insert(0, f"[{alert['timestamp'][:19]}] {alert['device']}: {alert['message']}")
#             if len(st.session_state.live_alerts) > 50:  # Prune old
#                 st.session_state.live_alerts.pop()
#         else:  # Sensor data
#             data = json.loads(msg.payload.decode())
#             new_row = pd.DataFrame([data])
#             new_row["timestamp"] = pd.to_datetime(new_row["timestamp"])
#             st.session_state.live_sensor_data = pd.concat([st.session_state.live_sensor_data, new_row], ignore_index=True)
#             if len(st.session_state.live_sensor_data) > 1000:  # Rolling window
#                 st.session_state.live_sensor_data = st.session_state.live_sensor_data.tail(1000)
#     except Exception as e:
#         print(f"❌ Dashboard MQTT error: {e}")

# def start_mqtt_thread():
#     if st.session_state.mqtt_client is None:
#         client = mqtt.Client()
#         client.on_connect = on_connect
#         client.on_message = on_message
#         client.connect(MQTT_BROKER, MQTT_PORT, 60)
#         st.session_state.mqtt_client = client
#         thread = threading.Thread(target=client.loop_forever, daemon=True)
#         thread.start()
#         st.session_state.mqtt_thread = thread
#         st.session_state.mqtt_connected = False

# # Start MQTT on first load
# start_mqtt_thread()

# # === Load Static Data ===
# @st.cache_data
# def load_anomalies():
#     try:
#         df = pd.read_csv(ANOMALY_PATH)
#         df["timestamp"] = pd.to_datetime(df["timestamp"])
#         return df
#     except FileNotFoundError:
#         return pd.DataFrame()

# # === UI Sections ===
# st.sidebar.header("Navigation")
# section = st.sidebar.radio("Go to:", ["Live Sensors", "Anomaly Detection", "Live Alerts", "Historical Data"])

# # Device selector (uses live data)
# devices = sorted(st.session_state.live_sensor_data["device"].unique())
# selected_device = st.sidebar.selectbox("Select Device", devices)

# # Auto-refresh
# auto_refresh = st.sidebar.checkbox("Auto-refresh every 10s", value=True)
# refresh_rate = 10 if auto_refresh else 0

# device_data = st.session_state.live_sensor_data[st.session_state.live_sensor_data["device"] == selected_device]

# if section == "Live Sensors":
#     st.subheader(f"📈 Live Sensor Readings — {selected_device}")
#     if st.session_state.mqtt_connected:
#         st.success("🔴 Live MQTT feed active!")
#     else:
#         st.warning("⚠️ Connecting to MQTT...")
    
#     # Live chart
#     if not device_data.empty:
#         chart_data = device_data.set_index("timestamp")[["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]]
#         st.line_chart(chart_data, use_container_width=True)
    
#     st.markdown("**Live Summary**")
#     st.metric("Current Temp (°C)", device_data["temperature_C"].iloc[-1] if not device_data.empty else 0)
#     st.metric("Current Power (W)", device_data["power_W"].iloc[-1] if not device_data.empty else 0)
    
#     # Raw live feed (last 5 messages)
#     st.subheader("📡 Recent MQTT Messages")
#     recent = device_data.tail(5)[["timestamp", "temperature_C", "CO_ppm", "power_W"]]
#     st.dataframe(recent)

# elif section == "Anomaly Detection":
#     anomalies = load_anomalies()
#     if anomalies.empty:
#         st.warning("No anomaly data available yet. Run training to generate.")
#     else:
#         st.subheader(f"🚨 Anomalies — {selected_device}")
#         dev_anom = anomalies[anomalies["device"] == selected_device]
#         if not dev_anom.empty:
#             fig, ax = plt.subplots(figsize=(12, 6))
#             ax.plot(dev_anom["timestamp"], dev_anom["temperature_C"], label="Temperature", alpha=0.7)
#             anomalies_points = dev_anom[dev_anom["anomaly"] == 1]
#             ax.scatter(
#                 anomalies_points["timestamp"],
#                 anomalies_points["temperature_C"],
#                 color="red", s=100, label="Anomaly", zorder=5
#             )
#             ax.set_xlabel("Time")
#             ax.set_ylabel("Temperature (°C)")
#             ax.legend()
#             ax.set_title(f"Temperature Anomalies for {selected_device}")
#             st.pyplot(fig)
#         else:
#             st.info("No anomalies for this device yet.")

# elif section == "Live Alerts":
#     st.subheader("🔔 Live System Alerts")
#     if st.session_state.mqtt_connected:
#         st.success("Receiving live alerts via MQTT!")
    
#     if not st.session_state.live_alerts:
#         st.info("No live alerts yet. Simulate a spike (e.g., high CO) to trigger.")
#     else:
#         for alert in st.session_state.live_alerts[-20:]:  # Last 20
#             st.error(alert)
    
#     # Fallback historical alerts
#     st.markdown("---")
#     st.caption("Historical (file-based) alerts:")
#     if os.path.exists(ALERT_LOG):
#         with open(ALERT_LOG, "r") as f:
#             hist_alerts = [line.strip() for line in f.readlines()[-10:]]  # Last 10
#         for line in hist_alerts:
#             st.warning(line)

# elif section == "Historical Data":
#     # Your original "Sensor Data" section, unchanged for batch view
#     st.subheader(f"📊 Historical Readings — {selected_device}")
#     st.line_chart(device_data.set_index("timestamp")[["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]])
#     st.markdown("**Summary Statistics**")
#     st.dataframe(device_data.describe().round(2))

# # Auto-rerun for live updates
# if auto_refresh:
#     time.sleep(refresh_rate)
#     st.rerun()

# # Footer
# st.markdown("---")
# st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")


import os
import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import json
import threading
import time
from datetime import datetime
import paho.mqtt.client as mqtt

base_dir = os.path.dirname(os.path.abspath(__file__))
ALERT_LOG = os.getenv('ALERTS_PATH', os.path.join(base_dir, "../alerts")) + "/alert_log.txt"  # Env fallback
DB_PATH = os.getenv('DB_PATH', '/app/kitchen.db')  # Env var
ANOMALY_PATH = os.getenv('MODELS_PATH', os.path.join(base_dir, "../models")) + "/results/anomaly_results.csv"  # Env fallback

# MQTT config
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_PREFIX = 'smart_kitchen/'
ALERT_TOPIC = MQTT_PREFIX + 'alerts'

st.set_page_config(page_title="Smart Kitchen Dashboard", layout="wide")

st.title("🍳 Smart Kitchen Monitoring Dashboard (MQTT Live Mode)")
st.markdown("Real-time IoT sensor streaming, anomalies, and instant alerts via MQTT.")

# === Global Setup ===
if 'live_sensor_data' not in st.session_state:
    # Initialize with historical DB data
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 500", conn)  # Last 500 for perf
    conn.close()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    st.session_state.live_sensor_data = df.sort_values('timestamp')

if 'live_alerts' not in st.session_state:
    st.session_state.live_alerts = []

if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = None
    st.session_state.mqtt_thread = None

# === MQTT Live Updater ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.mqtt_connected = True
        print("✅ MQTT connected for dashboard.")
        devices = ["refrigerator", "oven", "microwave"]
        for device in devices:
            topic = MQTT_PREFIX + device
            client.subscribe(topic)
        client.subscribe(ALERT_TOPIC)
    else:
        st.session_state.mqtt_connected = False
        print(f"❌ MQTT connect failed: {rc}")

def on_message(client, userdata, msg):
    try:
        if msg.topic == ALERT_TOPIC:
            alert = json.loads(msg.payload.decode())
            st.session_state.live_alerts.insert(0, f"[{alert['timestamp'][:19]}] {alert['device']}: {alert['message']}")
            if len(st.session_state.live_alerts) > 50:  # Prune old
                st.session_state.live_alerts.pop()
        else:  # Sensor data
            data = json.loads(msg.payload.decode())
            new_row = pd.DataFrame([data])
            new_row["timestamp"] = pd.to_datetime(new_row["timestamp"])
            st.session_state.live_sensor_data = pd.concat([st.session_state.live_sensor_data, new_row], ignore_index=True)
            if len(st.session_state.live_sensor_data) > 1000:  # Rolling window
                st.session_state.live_sensor_data = st.session_state.live_sensor_data.tail(1000)
    except Exception as e:
        print(f"❌ Dashboard MQTT error: {e}")

def start_mqtt_thread():
    if st.session_state.mqtt_client is None:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        st.session_state.mqtt_client = client
        thread = threading.Thread(target=client.loop_forever, daemon=True)
        thread.start()
        st.session_state.mqtt_thread = thread
        st.session_state.mqtt_connected = False

# Start MQTT on first load
start_mqtt_thread()

# === Load Static Data ===
@st.cache_data
def load_anomalies():
    try:
        df = pd.read_csv(ANOMALY_PATH)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

# === UI Sections ===
st.sidebar.header("Navigation")
section = st.sidebar.radio("Go to:", ["Live Sensors", "Anomaly Detection", "Live Alerts", "Historical Data"])

# Device selector (uses live data)
devices = sorted(st.session_state.live_sensor_data["device"].unique())
selected_device = st.sidebar.selectbox("Select Device", devices)

# Auto-refresh
auto_refresh = st.sidebar.checkbox("Auto-refresh every 10s", value=True)
refresh_rate = 10 if auto_refresh else 0

device_data = st.session_state.live_sensor_data[st.session_state.live_sensor_data["device"] == selected_device]

if section == "Live Sensors":
    st.subheader(f"📈 Live Sensor Readings — {selected_device}")
    if st.session_state.mqtt_connected:
        st.success("🔴 Live MQTT feed active!")
    else:
        st.warning("⚠️ Connecting to MQTT...")
    
    # Live chart
    if not device_data.empty:
        chart_data = device_data.set_index("timestamp")[["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]]
        st.line_chart(chart_data, use_container_width=True)
    
    st.markdown("**Live Summary**")
    st.metric("Current Temp (°C)", device_data["temperature_C"].iloc[-1] if not device_data.empty else 0)
    st.metric("Current Power (W)", device_data["power_W"].iloc[-1] if not device_data.empty else 0)
    
    # Raw live feed (last 5 messages)
    st.subheader("📡 Recent MQTT Messages")
    recent = device_data.tail(5)[["timestamp", "temperature_C", "CO_ppm", "power_W"]]
    st.dataframe(recent)

elif section == "Anomaly Detection":
    anomalies = load_anomalies()
    if anomalies.empty:
        st.warning("No anomaly data available yet. Run training to generate.")
    else:
        st.subheader(f"🚨 Anomalies — {selected_device}")
        dev_anom = anomalies[anomalies["device"] == selected_device]
        if not dev_anom.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(dev_anom["timestamp"], dev_anom["temperature_C"], label="Temperature", alpha=0.7)
            anomalies_points = dev_anom[dev_anom["anomaly"] == 1]
            ax.scatter(
                anomalies_points["timestamp"],
                anomalies_points["temperature_C"],
                color="red", s=100, label="Anomaly", zorder=5
            )
            ax.set_xlabel("Time")
            ax.set_ylabel("Temperature (°C)")
            ax.legend()
            ax.set_title(f"Temperature Anomalies for {selected_device}")
            st.pyplot(fig)
        else:
            st.info("No anomalies for this device yet.")

elif section == "Live Alerts":
    st.subheader("🔔 Live System Alerts")
    if st.session_state.mqtt_connected:
        st.success("Receiving live alerts via MQTT!")
    
    if not st.session_state.live_alerts:
        st.info("No live alerts yet. Simulate a spike (e.g., high CO) to trigger.")
    else:
        for alert in st.session_state.live_alerts[-20:]:  # Last 20
            st.error(alert)
    
    # Fallback historical alerts
    st.markdown("---")
    st.caption("Historical (file-based) alerts:")
    if os.path.exists(ALERT_LOG):
        with open(ALERT_LOG, "r") as f:
            hist_alerts = [line.strip() for line in f.readlines()[-10:]]  # Last 10
        for line in hist_alerts:
            st.warning(line)

elif section == "Historical Data":
    # Your original "Sensor Data" section, unchanged for batch view
    st.subheader(f"📊 Historical Readings — {selected_device}")
    st.line_chart(device_data.set_index("timestamp")[["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]])
    st.markdown("**Summary Statistics**")
    st.dataframe(device_data.describe().round(2))

# Auto-rerun for live updates
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
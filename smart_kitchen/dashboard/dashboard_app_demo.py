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
import ssl  # For IoT Core TLS
import streamlit_authenticator as stauth  # For customer auth

base_dir = os.path.dirname(os.path.abspath(__file__))
ALERT_LOG = os.getenv('ALERTS_PATH', os.path.join(base_dir, "../alerts")) + "/alert_log.txt"
DB_PATH = os.getenv('DB_PATH', '/app/kitchen.db')
ANOMALY_PATH = os.getenv('MODELS_PATH', os.path.join(base_dir, "../models")) + "/results/anomaly_results.csv"

# IoT Core config
MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
CA_PATH = os.getenv('CA_PATH', '')
CERT_PATH = os.getenv('CERT_PATH', '')
KEY_PATH = os.getenv('KEY_PATH', '')
MQTT_PREFIX = 'smart_kitchen/'
ALERT_TOPIC = MQTT_PREFIX + 'alerts'

st.set_page_config(page_title="Smart Kitchen Dashboard", layout="wide")

st.title("🍳 Smart Kitchen Monitoring Dashboard (AWS IoT Core Live Mode)")
st.markdown("Real-time IoT sensor streaming, anomalies, and instant alerts via AWS IoT Core.")

# # === Auth Setup (Customer Login) ===
# credentials_str = os.getenv('CREDENTIALS', None)
# if not credentials_str or credentials_str.strip() == '':
#     # Fallback to valid hardcoded (no env quote issues)
#     credentials_str = '{"usernames":{"demo":{"name":"Demo User","hashed_password":"$2b$12$shpp83iTe6i1h4QUAhZktO5aQ1erI82AGUWxV3mdgL53Vs0xZrLMu"}}}'
# try:
#     credentials = json.loads(credentials_str)
# except json.JSONDecodeError as e:
#     st.error(f"Invalid credentials JSON: {e}. Using fallback.")
#     credentials = {"usernames":{"demo":{"name":"Demo User","hashed_password":"$2b$12$shpp83iTe6i1h4QUAhZktO5aQ1erI82AGUWxV3mdgL53Vs0xZrLMu"}}}

# cookie_str = os.getenv('COOKIE', '{"name":"smart_kitchen","key":"random_key_2025","expiry_days":30}')
# try:
#     cookie_dict = json.loads(cookie_str)
# except json.JSONDecodeError:
#     cookie_dict = {"name":"smart_kitchen","key":"random_key_2025","expiry_days":30}

# authenticator = stauth.Authenticate(
#     credentials=credentials,
#     cookie_name=cookie_dict.get('name', 'some_cookie_name'),
#     cookie_key=cookie_dict.get('key', 'some_key'),
#     cookie_expiry_days=cookie_dict.get('expiry_days', 30),
#     preauthorized=None
# )

# # Render login
# authenticator.login(location='main')

# if st.session_state["authentication_status"]:
#     name = st.session_state["name"]
#     username = st.session_state["username"]
#     tenant_id = username if username else 'default'
    
#     # Deduped welcome (flag in session)
#     if not st.session_state.get('welcome_shown', False):
#         st.session_state.welcome_shown = True
#         st.sidebar.success(f'Welcome, {name}! Logged in as tenant: **{tenant_id}**')
    
#     # Logout with key
#     authenticator.logout('Logout', 'sidebar', key='unique_logout_key')
    
# elif st.session_state["authentication_status"] is False:
#     st.error('Username/password is incorrect')
#     st.session_state.clear()  # Clear bad session
#     st.rerun()
# else:
#     st.stop()

# === Auth Setup (Customer Login) ===
credentials_str = os.getenv('CREDENTIALS', None)
if not credentials_str or credentials_str.strip() == '':
    # Fallback to plain text for demo (easy, no hash issues)
    credentials_str = '{"usernames":{"demo":{"name":"Demo User","password":"demo123"}}}'
try:
    credentials = json.loads(credentials_str)
    # Validate dict has 'password' or 'hashed_password'
    if 'usernames' not in credentials or 'demo' not in credentials['usernames']:
        raise ValueError("Invalid credentials structure")
    user_creds = credentials['usernames']['demo']
    if 'hashed_password' not in user_creds and 'password' not in user_creds:
        raise ValueError("No 'password' or 'hashed_password' in user dict")
except (json.JSONDecodeError, ValueError) as e:
    st.error(f"Auth config error: {e}. Using plain demo fallback.")
    credentials = {"usernames":{"demo":{"name":"Demo User","password":"demo123"}}}

cookie_str = os.getenv('COOKIE', '{"name":"smart_kitchen","key":"random_key_2025","expiry_days":30}')
try:
    cookie_dict = json.loads(cookie_str)
except json.JSONDecodeError:
    cookie_dict = {"name":"smart_kitchen","key":"random_key_2025","expiry_days":30}

authenticator = stauth.Authenticate(
    credentials=credentials,
    cookie_name=cookie_dict.get('name', 'some_cookie_name'),
    cookie_key=cookie_dict.get('key', 'some_key'),
    cookie_expiry_days=cookie_dict.get('expiry_days', 30),
    preauthorized=None
)

# Render login
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    name = st.session_state["name"]
    username = st.session_state["username"]
    tenant_id = username if username else 'demo'
    
    # Deduped welcome
    if not st.session_state.get('welcome_shown', False):
        st.session_state.welcome_shown = True
        st.sidebar.success(f'Welcome, {name}! Logged in as tenant: **{tenant_id}**')
    
    authenticator.logout('Logout', 'sidebar', key='unique_logout_key')
    
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
    st.session_state.clear()
    st.rerun()
else:
    st.stop()

# === Global Setup (Tenant-Filtered) ===
if 'live_sensor_data' not in st.session_state:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sensor_data)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'tenant_id' in columns:
            df = pd.read_sql("SELECT * FROM sensor_data WHERE tenant_id = ? OR tenant_id IS NULL ORDER BY timestamp DESC LIMIT 500", conn, params=[tenant_id])
        else:
            df = pd.read_sql("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 500", conn)
            df['tenant_id'] = 'default'
        conn.close()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        st.session_state.live_sensor_data = df.sort_values('timestamp') if not df.empty else pd.DataFrame()
    except Exception as e:
        st.error(f"DB load error: {e}")
        st.session_state.live_sensor_data = pd.DataFrame()

if 'live_alerts' not in st.session_state:
    st.session_state.live_alerts = []

if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = None
    st.session_state.mqtt_thread = None
    st.session_state.mqtt_connected = False

# start_mqtt_thread()

# === MQTT Live Updater ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.mqtt_connected = True
        print("✅ MQTT connected.")
        devices = ["refrigerator", "oven", "microwave"]
        for device in devices:
            topic = f"{tenant_id}/{MQTT_PREFIX}{device}"
            client.subscribe(topic)
        client.subscribe(ALERT_TOPIC)
    else:
        st.session_state.mqtt_connected = False
        print(f"❌ MQTT failed: {rc}")

def on_message(client, userdata, msg):
    try:
        if msg.topic == ALERT_TOPIC:
            alert = json.loads(msg.payload.decode())
            st.session_state.live_alerts.insert(0, f"[{alert['timestamp'][:19]}] {alert['device']}: {alert['message']}")
            if len(st.session_state.live_alerts) > 50:
                st.session_state.live_alerts.pop()
        else:
            data = json.loads(msg.payload.decode())
            data['tenant_id'] = tenant_id
            new_row = pd.DataFrame([data])
            new_row["timestamp"] = pd.to_datetime(new_row["timestamp"])
            st.session_state.live_sensor_data = pd.concat([st.session_state.live_sensor_data, new_row], ignore_index=True)
            if len(st.session_state.live_sensor_data) > 1000:
                st.session_state.live_sensor_data = st.session_state.live_sensor_data.tail(1000)
    except json.JSONDecodeError:
        print("Skipped invalid JSON")
    except Exception as e:
        print(f"❌ MQTT error: {e}")

# def start_mqtt_thread():
#     if st.session_state.mqtt_client is None:
#         client = mqtt.Client(client_id=f'smart-kitchen-dashboard-{tenant_id}')
#         if MQTT_ENDPOINT != 'localhost':
#             client.tls_set(
#                 ca_certs=CA_PATH,
#                 certfile=CERT_PATH,
#                 keyfile=KEY_PATH,
#                 cert_reqs=ssl.CERT_REQUIRED,
#                 tls_version=ssl.PROTOCOL_TLSv1_2
#             )
#         client.on_connect = on_connect
#         client.on_message = on_message
#         client.connect(MQTT_ENDPOINT, MQTT_PORT, 60)
#         st.session_state.mqtt_client = client
#         thread = threading.Thread(target=client.loop_forever, daemon=True)
#         thread.start()
#         st.session_state.mqtt_thread = thread

def start_mqtt_thread():
    if st.session_state.mqtt_client is None:
        client = mqtt.Client(client_id=f'smart-kitchen-dashboard-{tenant_id}')
        if MQTT_ENDPOINT != 'localhost':
            client.tls_set(
                ca_certs=CA_PATH,
                certfile=CERT_PATH,
                keyfile=KEY_PATH,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )
        
        # Debug print (remove after fix)
        print(f"🔍 Connecting to MQTT_ENDPOINT={MQTT_ENDPOINT}:{MQTT_PORT} with certs: CA={CA_PATH}, CERT={CERT_PATH}, KEY={KEY_PATH}")
        
        try:
            client.connect(MQTT_ENDPOINT, MQTT_PORT, 60)
            print("✅ MQTT connect attempted—check logs for on_connect callback.")
        except ConnectionRefusedError as e:
            print(f"❌ MQTT connection refused: {e}. Check endpoint, certs, or network.")
            st.warning("MQTT connection failed—fallback to historical data.")
            st.session_state.mqtt_connected = False
            return  # Skip thread
        
        client.on_connect = on_connect
        client.on_message = on_message
        thread = threading.Thread(target=client.loop_forever, daemon=True)
        thread.start()
        st.session_state.mqtt_thread = thread
        st.session_state.mqtt_client = client

start_mqtt_thread()

# === Load Static Data ===
@st.cache_data
def load_anomalies(_tenant_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(anomalies)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'tenant_id' in columns:
            df = pd.read_sql("SELECT * FROM anomalies WHERE tenant_id = ? OR tenant_id IS NULL", conn, params=[_tenant_id])
        else:
            df = pd.read_sql("SELECT * FROM anomalies", conn)
            df['tenant_id'] = 'default'
        conn.close()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except Exception:
        return pd.DataFrame()

# === UI Sections ===
st.sidebar.header("Navigation")
section = st.sidebar.radio("Go to:", ["Live Sensors", "Anomaly Detection", "Usage Predictor", "Live Alerts", "Historical Data"])

devices = sorted(st.session_state.live_sensor_data["device"].unique()) if not st.session_state.live_sensor_data.empty else ["refrigerator"]
selected_device = st.sidebar.selectbox("Select Device", devices, index=0)

auto_refresh = st.sidebar.checkbox("Auto-refresh every 10s", value=True)
refresh_rate = 10 if auto_refresh else 0

# Tenant-filtered device data (safe for empty DF)
if not st.session_state.live_sensor_data.empty:
    if 'tenant_id' in st.session_state.live_sensor_data.columns:
        device_data = st.session_state.live_sensor_data[
            (st.session_state.live_sensor_data["device"] == selected_device) & 
            (st.session_state.live_sensor_data["tenant_id"] == tenant_id)
        ]
    else:
        device_data = st.session_state.live_sensor_data[st.session_state.live_sensor_data["device"] == selected_device]
else:
    device_data = pd.DataFrame()  # Empty fallback

# device_data = st.session_state.live_sensor_data[
#     (st.session_state.live_sensor_data["device"] == selected_device) & 
#     (st.session_state.live_sensor_data["tenant_id"] == tenant_id)
# ] if 'tenant_id' in st.session_state.live_sensor_data.columns else st.session_state.live_sensor_data[st.session_state.live_sensor_data["device"] == selected_device]

st.sidebar.markdown("### 🔌 Integrations")
if st.sidebar.button("Sync to Home Assistant"):
    st.info("Bridging to HA...")
    st.balloons()
if st.sidebar.button("Send Alert to Google Home"):
    st.info("Pushing to Google Home...")
    st.balloons()

if section == "Live Sensors":
    st.subheader(f"📈 Live Readings — {selected_device} (Tenant: {tenant_id})")
    if st.session_state.mqtt_connected:
        st.success("🔴 Live feed active!")
    else:
        st.warning("⚠️ Connecting...")
    
    if not device_data.empty:
        chart_data = device_data.set_index("timestamp")[["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]]
        st.line_chart(chart_data, use_container_width=True)
        st.metric("Current Temp (°C)", device_data["temperature_C"].iloc[-1])
        st.metric("Current Power (W)", device_data["power_W"].iloc[-1])
        st.dataframe(device_data.tail(5)[["timestamp", "temperature_C", "CO_ppm", "power_W"]])
    else:
        st.info("No data yet.")

elif section == "Anomaly Detection":
    anomalies = load_anomalies(tenant_id)
    st.subheader(f"🚨 Anomalies — {selected_device} (Tenant: {tenant_id})")
    if anomalies.empty:
        st.warning("No anomaly data yet.")
    else:
        dev_anom = anomalies[(anomalies["device"] == selected_device) & (anomalies["tenant_id"] == tenant_id)]
        if not dev_anom.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(dev_anom["timestamp"], dev_anom["temperature_C"], label="Temperature", alpha=0.7)
            anomalies_points = dev_anom[dev_anom["anomaly"] == 1]
            ax.scatter(anomalies_points["timestamp"], anomalies_points["temperature_C"], color="red", s=100, label="Anomaly", zorder=5)
            ax.set_xlabel("Time")
            ax.set_ylabel("Temperature (°C)")
            ax.legend()
            ax.set_title(f"Anomalies for {selected_device}")
            st.pyplot(fig)
        else:
            st.info("No anomalies.")

elif section == "Usage Predictor":
    st.subheader(f"🔮 Predictor (Tenant: {tenant_id})")
    try:
        models_path = os.getenv('MODELS_PATH', '/app/models')
        pred_df = pd.read_csv(os.path.join(models_path, f'{tenant_id}_predictions.csv'))
        pred_df["timestamp"] = pd.to_datetime(pred_df["timestamp"])
        st.line_chart(pred_df.set_index("timestamp")[["predicted_usage", "confidence"]])
        st.metric("Next Week Usage", f"{pred_df['predicted_usage'].mean():.1f} kWh")
    except FileNotFoundError:
        st.warning("Run training for predictions.")
        demo_dates = pd.date_range(start=datetime.now(), periods=7, freq='D')
        demo_pred = pd.DataFrame({'timestamp': demo_dates, 'predicted_usage': [10 + i for i in range(7)]})
        st.line_chart(demo_pred.set_index("timestamp")["predicted_usage"])

elif section == "Live Alerts":
    st.subheader(f"🔔 Alerts (Tenant: {tenant_id})")
    if st.session_state.mqtt_connected:
        st.success("Receiving alerts!")
    if not st.session_state.live_alerts:
        st.info("No alerts yet.")
    else:
        for alert in st.session_state.live_alerts[-20:]:
            st.error(alert)
    if os.path.exists(ALERT_LOG):
        with open(ALERT_LOG, "r") as f:
            hist_alerts = [line.strip() for line in f.readlines()[-10:] if tenant_id in line or 'default' in line]
        for line in hist_alerts:
            st.warning(line)

elif section == "Historical Data":
    st.subheader(f"📊 Historical — {selected_device} (Tenant: {tenant_id})")
    if not device_data.empty:
        st.line_chart(device_data.set_index("timestamp")[["temperature_C", "CO_ppm", "CO2_ppm", "power_W"]])
        st.dataframe(device_data.describe().round(2))
    else:
        st.info("No historical data.")

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

st.markdown("---")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Tenant: {tenant_id} | MQTT: {MQTT_ENDPOINT}:{MQTT_PORT}")
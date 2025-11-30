import os
import sys
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

# Add the src directory to Python's module search path
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from anomaly_detection.detect_anomaly import detect_anomalies  # Import for on-the-fly detection
from predictive_maintenance.train_predictor import train_predictive_model  # Import for predictions

base_dir = os.path.dirname(os.path.abspath(__file__))
ALERT_LOG = os.getenv('ALERTS_PATH', os.path.join(base_dir, "../alerts")) + "/alert_log.txt"
DB_PATH = os.getenv('DB_PATH', '/app/smart_home.db')  # Updated DB path
ANOMALY_PATH = os.getenv('MODELS_PATH', os.path.join(base_dir, "../models")) + "/results/anomaly_results.csv"  # Assuming saved CSV for anomalies

# IoT Core config
MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
CA_PATH = os.getenv('CA_PATH', '')
CERT_PATH = os.getenv('CERT_PATH', '')
KEY_PATH = os.getenv('KEY_PATH', '')
MQTT_PREFIX = 'smart_home/'  # Updated prefix
ALERT_TOPIC = MQTT_PREFIX + 'alerts'  # Updated alert topic

st.set_page_config(page_title="Smart Home Insurance Dashboard", layout="wide")

st.title("🏠 Smart Home Insurance Monitoring Dashboard (AWS IoT Core Live Mode)")
st.markdown("Real-time IoT sensor streaming for property risk assessment, anomalies, and instant alerts via AWS IoT Core.")

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

cookie_str = os.getenv('COOKIE', '{"name":"smart_home","key":"random_key_2025","expiry_days":30}')
try:
    cookie_dict = json.loads(cookie_str)
except json.JSONDecodeError:
    cookie_dict = {"name":"smart_home","key":"random_key_2025","expiry_days":30}

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
        # Parse readings JSON for easier handling
        parsed_rows = []
        for _, row in df.iterrows():
            try:
                readings = json.loads(row['readings'])
                parsed_row = row.copy()
                parsed_row['readings'] = readings  # Keep as dict for flexibility
                parsed_rows.append(parsed_row)
            except:
                pass  # Skip invalid
        st.session_state.live_sensor_data = pd.DataFrame(parsed_rows).sort_values('timestamp') if parsed_rows else pd.DataFrame()
    except Exception as e:
        st.error(f"DB load error: {e}")
        st.session_state.live_sensor_data = pd.DataFrame()

if 'live_alerts' not in st.session_state:
    st.session_state.live_alerts = []

if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = None
    st.session_state.mqtt_thread = None
    st.session_state.mqtt_connected = False

# === MQTT Live Updater ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        st.session_state.mqtt_connected = True
        print("✅ MQTT connected.")
        devices = ["smoke_detector", "water_sensor", "door_sensor", "temperature_sensor", "humidity_sensor", "motion_detector"]
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
            st.session_state.live_alerts.insert(0, f"[{alert['timestamp'][:19]}] {alert['device']}: {alert['message']} (Severity: {alert['severity']})")
            if len(st.session_state.live_alerts) > 50:
                st.session_state.live_alerts.pop()
        else:
            data = json.loads(msg.payload.decode())
            data['tenant_id'] = tenant_id
            new_row = pd.DataFrame([data])
            new_row["timestamp"] = pd.to_datetime(new_row["timestamp"])
            # Parse readings
            new_row['readings'] = [data['readings']]  # Already dict
            st.session_state.live_sensor_data = pd.concat([st.session_state.live_sensor_data, new_row], ignore_index=True)
            if len(st.session_state.live_sensor_data) > 1000:
                st.session_state.live_sensor_data = st.session_state.live_sensor_data.tail(1000)
    except json.JSONDecodeError:
        print("Skipped invalid JSON")
    except Exception as e:
        print(f"❌ MQTT error: {e}")

def start_mqtt_thread():
    if st.session_state.mqtt_client is None:
        client = mqtt.Client(client_id=f'smart-home-dashboard-{tenant_id}')
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
        # For demo, run detection on current data
        if not st.session_state.live_sensor_data.empty:
            filtered_df = st.session_state.live_sensor_data[st.session_state.live_sensor_data["tenant_id"] == _tenant_id]
            if not filtered_df.empty:
                anomalies_df = detect_anomalies(filtered_df)
                # Add back non-anomaly rows or just return anomalies
                anomalies_df["anomaly"] = -1  # Mark as anomaly
                return anomalies_df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# === UI Sections ===
st.sidebar.header("Navigation")
section = st.sidebar.radio("Go to:", ["Live Sensors", "Anomaly Detection", "Risk Predictor", "Live Alerts", "Historical Data"])

devices = sorted(st.session_state.live_sensor_data["device"].unique()) if not st.session_state.live_sensor_data.empty else ["smoke_detector"]
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

st.sidebar.markdown("### 🔌 Integrations")
if st.sidebar.button("Sync to Insurance Portal"):
    st.info("Bridging to insurance CRM...")
    st.balloons()
if st.sidebar.button("Send Alert to Policyholder App"):
    st.info("Pushing to mobile app...")
    st.balloons()

if section == "Live Sensors":
    st.subheader(f"📈 Live Readings — {selected_device} (Tenant: {tenant_id})")
    if st.session_state.mqtt_connected:
        st.success("🔴 Live feed active!")
    else:
        st.warning("⚠️ Connecting...")
    
    if not device_data.empty:
        latest = device_data.iloc[-1]
        readings = latest['readings']
        # Device-specific metrics
        col1, col2, col3, col4 = st.columns(4)
        if selected_device == "smoke_detector":
            col1.metric("Smoke (ppm)", readings.get('smoke_ppm', 0))
            col2.metric("Alarm", "Active" if readings.get('alarm', False) else "Clear")
        elif selected_device == "water_sensor":
            col1.metric("Moisture (%)", readings.get('moisture_percent', 0))
            col2.metric("Leak", "Detected" if readings.get('leak_detected', False) else "None")
        elif selected_device == "temperature_sensor":
            col1.metric("Temp (°C)", readings.get('temp_C', 21))
        elif selected_device == "humidity_sensor":
            col1.metric("Humidity (%)", readings.get('humidity_percent', 50))
        elif selected_device == "door_sensor":
            col1.metric("State", readings.get('state', 'closed').title())
        elif selected_device == "motion_detector":
            col1.metric("Motion", "Detected" if readings.get('motion_detected', False) else "None")
        
        # Simple time series for common fields (e.g., temp if available)
        numeric_readings = pd.json_normalize(device_data['readings'])
        common_cols = [col for col in numeric_readings.columns if col in ['temp_C', 'humidity_percent', 'smoke_ppm', 'moisture_percent']]
        if common_cols:
            chart_data = pd.concat([device_data[['timestamp']], numeric_readings[common_cols]], axis=1)
            st.line_chart(chart_data.set_index("timestamp")[common_cols], use_container_width=True)
        
        st.dataframe(device_data.tail(5)[["timestamp", "readings"]])
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
            # Extract numeric for plot (e.g., temp_C)
            numeric_readings = pd.json_normalize(dev_anom['readings'])
            if 'temp_C' in numeric_readings.columns:
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(dev_anom["timestamp"], numeric_readings["temp_C"], label="Temperature", alpha=0.7)
                ax.scatter(dev_anom["timestamp"], numeric_readings["temp_C"], color="red", s=100, label="Anomaly", zorder=5)
                ax.set_xlabel("Time")
                ax.set_ylabel("Temperature (°C)")
                ax.legend()
                ax.set_title(f"Anomalies for {selected_device}")
                st.pyplot(fig)
            else:
                st.dataframe(dev_anom)
        else:
            st.info("No anomalies.")

elif section == "Risk Predictor":
    st.subheader(f"🔮 Risk Predictor (Tenant: {tenant_id})")
    try:
        # Run model on current data
        if not device_data.empty:
            model = train_predictive_model(device_data)
            # For demo, predict on latest
            latest_features, _ = prepare_features_and_labels(pd.DataFrame([device_data.iloc[-1]]))  # Assuming helper from train_predictor
            risk_prob = model.predict_proba(latest_features)[0][1]
            st.metric("Predicted Risk Level", f"{risk_prob:.2%}")
            st.success("Low risk - No immediate action needed." if risk_prob < 0.5 else "High risk - Review policy.")
        else:
            st.warning("No data for prediction.")
    except Exception as e:
        st.warning(f"Run training for predictions: {e}")
        demo_dates = pd.date_range(start=datetime.now(), periods=7, freq='D')
        demo_risk = pd.DataFrame({'timestamp': demo_dates, 'risk_level': [0.1 + i*0.1 for i in range(7)]})
        st.line_chart(demo_risk.set_index("timestamp")["risk_level"])

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
        numeric_readings = pd.json_normalize(device_data['readings'])
        common_cols = [col for col in numeric_readings.columns if col in ['temp_C', 'humidity_percent', 'smoke_ppm', 'moisture_percent']]
        if common_cols:
            chart_data = pd.concat([device_data[['timestamp']], numeric_readings[common_cols]], axis=1)
            st.line_chart(chart_data.set_index("timestamp")[common_cols])
        st.dataframe(device_data.describe(include='all').round(2))  # Adjust for mixed types
    else:
        st.info("No historical data.")

if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

st.markdown("---")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Tenant: {tenant_id} | MQTT: {MQTT_ENDPOINT}:{MQTT_PORT}")
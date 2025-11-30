# alert_system.py (Modified for Smart Home Property Insurance Demo)

import os
import json
import time
import requests
import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime
import ssl

# -------- ENV --------
DB_PATH = os.getenv('DB_PATH', '/app/smart_home.db')  # Updated DB path
ALERTS_PATH = os.getenv('ALERTS_PATH', '/app/alerts')
MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
CA_PATH = os.getenv('CA_PATH', '')
CERT_PATH = os.getenv('CERT_PATH', '')
KEY_PATH = os.getenv('KEY_PATH', '')
MQTT_PREFIX = 'smart_home/'  # Updated prefix
ALERT_TOPIC = f"{MQTT_PREFIX}alerts"  # Updated alert topic
TENANT_ID = os.getenv('TENANT_ID', 'demo')

FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "YOUR_SERVER_KEY")

# -------- FCM PUSH --------
def send_push_to_tenant(tenant_id, title, body):
    """Send push notification via FCM using stored tokens."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT token FROM fcm_tokens WHERE tenant_id = ?", (tenant_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("⚠ No FCM tokens found for tenant:", tenant_id)
        return

    for (token,) in rows:
        print(f"📨 Sending push to {tenant_id} -> {token}")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"key={FCM_SERVER_KEY}",
        }

        payload = {
            "to": token,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default"
            },
            "data": {
                "tenant_id": tenant_id,
                "type": "alert"
            }
        }

        requests.post("https://fcm.googleapis.com/fcm/send",
                      headers=headers,
                      json=payload)

# -------- DB SETUP --------
def init_alerts_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            device TEXT,
            message TEXT,
            severity TEXT DEFAULT 'warning',
            tenant_id TEXT DEFAULT 'demo'
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fcm_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT,
            token TEXT
        );
    """)

    conn.commit()
    conn.close()

    print("✅ Alerts DB initialized for smart home.")

# -------- MQTT HANDLERS --------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected for alerts.")
        devices = ["smoke_detector", "water_sensor", "door_sensor", "temperature_sensor", "humidity_sensor", "motion_detector"]
        for device in devices:
            topic = f"{TENANT_ID}/{MQTT_PREFIX}{device}"
            client.subscribe(topic)
            print(f"📥 Subscribed: {topic}")
    else:
        print("❌ Connect failed:", rc)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        device = data["device"]
        readings = data["readings"]  # JSON object for new format

        alert_message = None
        severity = "warning"

        if device == "smoke_detector":
            smoke = readings.get("smoke_ppm", 0)
            alarm = readings.get("alarm", False)
            if alarm or smoke > 50:
                alert_message = f"Smoke detected! {smoke}ppm - Potential fire risk."
                severity = "critical"
        elif device == "water_sensor":
            moisture = readings.get("moisture_percent", 0)
            leak = readings.get("leak_detected", False)
            if leak or moisture > 50:
                alert_message = f"Water leak detected! Moisture: {moisture}%."
                severity = "critical"
        elif device == "temperature_sensor":
            temp = readings.get("temp_C", 21)
            if temp < 10:
                alert_message = f"Freezing temperature: {temp}°C - Risk of pipe burst."
                severity = "warning"
            elif temp > 30:
                alert_message = f"High temperature: {temp}°C - Overheating risk."
                severity = "warning"
        elif device == "humidity_sensor":
            humidity = readings.get("humidity_percent", 50)
            if humidity > 70:
                alert_message = f"High humidity: {humidity}% - Mold risk alert."
                severity = "warning"
        elif device == "door_sensor":
            state = readings.get("state", "closed")
            if state == "open":
                alert_message = "Door left open - Security breach or ventilation issue."
                severity = "warning"
        elif device == "motion_detector":
            motion = readings.get("motion_detected", False)
            if motion:
                alert_message = "Unexpected motion detected - Potential intrusion."
                severity = "warning"

        if alert_message:
            # Save alert
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO alerts (timestamp, device, message, severity, tenant_id)
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, device, alert_message, severity, TENANT_ID))
            conn.commit()
            conn.close()

            # Write to file
            with open(os.path.join(ALERTS_PATH, "alert_log.txt"), "a") as f:
                f.write(f"[{timestamp}] {alert_message}\n")

            # MQTT publish
            alert = {
                "timestamp": timestamp,
                "device": device,
                "message": alert_message,
                "severity": severity,
                "tenant_id": TENANT_ID
            }
            client.publish(ALERT_TOPIC, json.dumps(alert))

            print(f"🚨 ALERT -> {alert_message}")

            # PUSH NOTIFICATION
            send_push_to_tenant(TENANT_ID, "Smart Home Alert", alert_message)

        # Print summary based on device
        if device == "smoke_detector":
            print(f"📊 Checked {device}: Smoke={readings.get('smoke_ppm', 0)}ppm, Alarm={readings.get('alarm', False)}")
        elif device == "water_sensor":
            print(f"📊 Checked {device}: Moisture={readings.get('moisture_percent', 0)}%, Leak={readings.get('leak_detected', False)}")
        elif device == "temperature_sensor":
            print(f"📊 Checked {device}: Temp={readings.get('temp_C', 21)}°C")
        elif device == "humidity_sensor":
            print(f"📊 Checked {device}: Humidity={readings.get('humidity_percent', 50)}%")
        elif device == "door_sensor":
            print(f"📊 Checked {device}: State={readings.get('state', 'closed')}")
        elif device == "motion_detector":
            print(f"📊 Checked {device}: Motion={readings.get('motion_detected', False)}")

    except Exception as e:
        print("❌ Error:", e)

# -------- MAIN LOOP --------
def run_alerts_system():
    init_alerts_db()

    client = mqtt.Client(client_id=f"alert-system-{TENANT_ID}")

    if MQTT_ENDPOINT != "localhost":
        client.tls_set(
            ca_certs=CA_PATH,
            certfile=CERT_PATH,
            keyfile=KEY_PATH,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2,
        )

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_ENDPOINT, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    run_alerts_system()
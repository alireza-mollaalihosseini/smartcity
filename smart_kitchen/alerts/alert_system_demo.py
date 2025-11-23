# import os
# import json
# import paho.mqtt.client as mqtt
# import ssl  # For IoT Core TLS
# from datetime import datetime
# from integrations import bridge_to_ha, send_to_google_home  # Import for consistency

# # IoT Core config
# MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
# MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
# CA_PATH = os.getenv('CA_PATH', '')
# CERT_PATH = os.getenv('CERT_PATH', '')
# KEY_PATH = os.getenv('KEY_PATH', '')
# MQTT_PREFIX = 'smart_kitchen/'
# ALERT_TOPIC = f"{os.getenv('TENANT_ID', 'default')}/{MQTT_PREFIX}alerts"  # Tenant-prefixed
# ALERT_LOG = os.getenv('ALERTS_PATH', '/app/alerts') + '/alert_log.txt'
# TENANT_ID = os.getenv('TENANT_ID', 'default')  # For consistency

# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print(f"✅ Connected to MQTT for alerts (IoT Core) for tenant {TENANT_ID}.")
#         client.subscribe(ALERT_TOPIC)
#     else:
#         print(f"❌ MQTT connect failed: {rc}")

# def on_message(client, userdata, msg):
#     if msg.topic == ALERT_TOPIC:
#         try:
#             alert = json.loads(msg.payload.decode())
#             alert['tenant_id'] = TENANT_ID  # Tag for consistency
#             timestamp = datetime.now().isoformat()
#             log_entry = f"[{timestamp}] Tenant {TENANT_ID} - {alert.get('device', 'Unknown')}: {alert.get('message', 'No message')}\n"
#             with open(ALERT_LOG, 'a') as f:
#                 f.write(log_entry)
#             print(f"🔔 Alert logged (Tenant: {TENANT_ID}): {log_entry.strip()}")
            
#             # Integrations: Bridge to HA & Google (for consistency with dashboard goals)
#             bridge_to_ha(alert, TENANT_ID)
#             send_to_google_home(alert.get('message', 'Alert'), alert.get('device', 'unknown'), TENANT_ID)
            
#             # Optional: Pub confirmation back
#             confirmation = {"status": "processed", "tenant_id": TENANT_ID}
#             client.publish(ALERT_TOPIC + "/ack", json.dumps(confirmation), qos=1)
#         except Exception as e:
#             print(f"❌ Alert processing error (Tenant: {TENANT_ID}): {e}")

# if __name__ == "__main__":
#     client = mqtt.Client(client_id=f'smart-kitchen-alerts-{TENANT_ID}')  # Unique with tenant
    
#     # TLS for IoT Core (skip if local)
#     if MQTT_ENDPOINT != 'localhost':
#         client.tls_set(
#             ca_certs=CA_PATH,
#             certfile=CERT_PATH,
#             keyfile=KEY_PATH,
#             cert_reqs=ssl.CERT_REQUIRED,
#             tls_version=ssl.PROTOCOL_TLSv1_2
#         )
    
#     client.on_connect = on_connect
#     client.on_message = on_message
#     client.connect(MQTT_ENDPOINT, MQTT_PORT, 60)
#     client.loop_forever()

# import os
# import json
# import time
# import paho.mqtt.client as mqtt
# import sqlite3
# from datetime import datetime
# import ssl  # For IoT Core TLS

# # Env vars
# DB_PATH = os.getenv('DB_PATH', '/app/kitchen.db')
# ALERTS_PATH = os.getenv('ALERTS_PATH', '/app/alerts')
# MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
# MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
# CA_PATH = os.getenv('CA_PATH', '')
# CERT_PATH = os.getenv('CERT_PATH', '')
# KEY_PATH = os.getenv('KEY_PATH', '')
# MQTT_PREFIX = 'smart_kitchen/'
# ALERT_TOPIC = f"{MQTT_PREFIX}alerts"
# TENANT_ID = os.getenv('TENANT_ID', 'demo')
# HA_BROKER = os.getenv('HA_BROKER', '')  # Optional HA URL
# GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')  # Stub

# # Stub integrations (no real module needed)
# def bridge_to_ha(device, alert_message):
#     """Stub for Home Assistant bridge."""
#     print(f"🔌 Stub: Bridging {device} alert '{alert_message}' to HA (broker: {HA_BROKER})")
#     # Real: Use mqtt to HA or API call

# def send_to_google_home(alert_message, device):
#     """Stub for Google Home alert."""
#     print(f"🔔 Stub: Sending '{alert_message}' for {device} to Google Home (client ID: {GOOGLE_CLIENT_ID})")
#     # Real: Use Google Smart Device Management API

# def init_alerts_db():
#     """Create alerts table if not exists."""
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS alerts (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             timestamp TEXT,
#             device TEXT,
#             message TEXT,
#             severity TEXT DEFAULT 'warning',
#             tenant_id TEXT DEFAULT 'demo'
#         )
#     """)
#     conn.commit()
#     conn.close()
#     print("✅ Alerts DB initialized.")

# def on_connect(client, userdata, flags, rc):
#     if rc == 0:
#         print("✅ Connected for alerts (IoT Core).")
#         # Subscribe to sensor topics for thresholds
#         devices = ["refrigerator", "oven", "microwave"]
#         for device in devices:
#             topic = f"{TENANT_ID}/{MQTT_PREFIX}{device}"
#             client.subscribe(topic)
#             print(f"📥 Subscribed to {topic} for alerts.")
#     else:
#         print(f"❌ Alerts connect failed: {rc}")

# def on_message(client, userdata, msg):
#     try:
#         data = json.loads(msg.payload.decode())
#         device = data['device']
#         temp = data['temperature_C']
#         co = data['CO_ppm']
        
#         # Threshold checks (customize)
#         alert_message = None
#         severity = 'warning'
#         if device == "oven" and temp > 200:
#             alert_message = f"High oven temp: {temp}°C - Risk of fire!"
#             severity = 'critical'
#         elif co > 50:
#             alert_message = f"High CO detected: {co}ppm on {device}!"
#             severity = 'warning'
        
#         if alert_message:
#             alert = {
#                 'timestamp': datetime.now().isoformat(),
#                 'device': device,
#                 'message': alert_message,
#                 'severity': severity,
#                 'tenant_id': TENANT_ID
#             }
#             # Log to file
#             with open(os.path.join(ALERTS_PATH, 'alert_log.txt'), 'a') as f:
#                 f.write(f"[{alert['timestamp']}]: {alert['message']} (Severity: {severity})\n")
            
#             # Publish alert
#             client.publish(ALERT_TOPIC, json.dumps(alert), qos=1)
#             print(f"🚨 Alert published: {alert_message} (Severity: {severity})")
            
#             # Stub integrations
#             bridge_to_ha(device, alert_message)
#             send_to_google_home(alert_message, device)
        
#         print(f"📊 Monitored {device}: Temp {temp}°C, CO {co}ppm - No alert.")
#     except Exception as e:
#         print(f"❌ Alerts error: {e}")

# def run_alerts_system():
#     init_alerts_db()
#     client = mqtt.Client(client_id=f'smart-kitchen-alerts-{TENANT_ID}')
    
#     if MQTT_ENDPOINT != 'localhost':
#         client.tls_set(
#             ca_certs=CA_PATH,
#             certfile=CERT_PATH,
#             keyfile=KEY_PATH,
#             cert_reqs=ssl.CERT_REQUIRED,
#             tls_version=ssl.PROTOCOL_TLSv1_2
#         )
    
#     client.on_connect = on_connect
#     client.on_message = on_message
#     client.connect(MQTT_ENDPOINT, MQTT_PORT, 60)
#     client.loop_forever()

# if __name__ == "__main__":
#     run_alerts_system()


import os
import json
import time
import requests
import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime
import ssl

# -------- ENV --------
DB_PATH = os.getenv('DB_PATH', '/app/kitchen.db')
ALERTS_PATH = os.getenv('ALERTS_PATH', '/app/alerts')
MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
CA_PATH = os.getenv('CA_PATH', '')
CERT_PATH = os.getenv('CERT_PATH', '')
KEY_PATH = os.getenv('KEY_PATH', '')
MQTT_PREFIX = 'smart_kitchen/'
ALERT_TOPIC = f"{MQTT_PREFIX}alerts"
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

    print("✅ Alerts DB initialized.")

# -------- MQTT HANDLERS --------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected for alerts.")
        for device in ["refrigerator", "oven", "microwave"]:
            topic = f"{TENANT_ID}/{MQTT_PREFIX}{device}"
            client.subscribe(topic)
            print(f"📥 Subscribed: {topic}")
    else:
        print("❌ Connect failed:", rc)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        device = data["device"]
        temp = data["temperature_C"]
        co = data["CO_ppm"]

        alert_message = None
        severity = "warning"

        if device == "oven" and temp > 200:
            alert_message = f"High oven temperature: {temp}°C!"
            severity = "critical"
        elif co > 50:
            alert_message = f"High CO detected: {co}ppm!"
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

            # PUSH NOTIFICATION (NEW)
            send_push_to_tenant(TENANT_ID, "Smart Kitchen Alert", alert_message)

        print(f"📊 Checked {device}: Temp={temp}, CO={co}")

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

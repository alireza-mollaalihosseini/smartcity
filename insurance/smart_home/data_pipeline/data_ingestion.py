# data_ingestion.py (Modified for Smart Home Property Insurance Demo)

import os
import json
import sqlite3
import paho.mqtt.client as mqtt
from pathlib import Path
import ssl  # For IoT Core TLS

DB_PATH = os.getenv('DB_PATH', '/app/smart_home.db')  # Updated DB name
MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
CA_PATH = os.getenv('CA_PATH', '')
CERT_PATH = os.getenv('CERT_PATH', '')
KEY_PATH = os.getenv('KEY_PATH', '')
MQTT_PREFIX = 'smart_home/'  # Updated for smart home
TENANT_ID = os.getenv('TENANT_ID', 'demo')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            device TEXT,
            readings TEXT,  -- JSON blob for flexible sensor readings
            tenant_id TEXT DEFAULT 'demo'
        )
    """)
    conn.commit()
    conn.close()
    print("✅ DB initialized with flexible readings support for smart home.")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected for ingestion.")
        devices = ["smoke_detector", "water_sensor", "door_sensor", "temperature_sensor", "humidity_sensor", "motion_detector"]
        for device in devices:
            topic = f"{TENANT_ID}/{MQTT_PREFIX}{device}"
            client.subscribe(topic)
            print(f"📥 Subscribed to {topic} for {TENANT_ID}")
    else:
        print(f"❌ Connect failed: {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        data['tenant_id'] = TENANT_ID
        readings_json = json.dumps(data['readings'])  # Store readings as JSON
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sensor_data (timestamp, device, readings, tenant_id)
            VALUES (?, ?, ?, ?)
        """, (
            data['timestamp'],
            data['device'],
            readings_json,
            data['tenant_id']
        ))
        conn.commit()
        conn.close()
        print(f"💾 Ingested ({TENANT_ID}): {data['device']} at {data['timestamp'][:19]} - Readings: {readings_json[:100]}...")
    except Exception as e:
        print(f"❌ Ingestion error: {e}")

def consume_and_ingest():
    init_db()
    client = mqtt.Client(client_id=f'smart-home-ingester-{TENANT_ID}')
    
    if MQTT_ENDPOINT != 'localhost':
        client.tls_set(
            ca_certs=CA_PATH,
            certfile=CERT_PATH,
            keyfile=KEY_PATH,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_ENDPOINT, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    consume_and_ingest()
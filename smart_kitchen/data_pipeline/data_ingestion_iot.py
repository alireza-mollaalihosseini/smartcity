import os
import json
import sqlite3
import paho.mqtt.client as mqtt
from pathlib import Path
import ssl  # For IoT Core TLS

# Env vars
DB_PATH = os.getenv('DB_PATH', '/app/kitchen.db')
MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
CA_PATH = os.getenv('CA_PATH', '')
CERT_PATH = os.getenv('CERT_PATH', '')
KEY_PATH = os.getenv('KEY_PATH', '')
MQTT_PREFIX = 'smart_kitchen/'

def init_db():
    """Create table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            device TEXT,
            temperature_C REAL,
            CO_ppm REAL,
            CO2_ppm REAL,
            power_W REAL
        )
    """)
    conn.commit()
    conn.close()

def on_connect(client, userdata, flags, rc):
    """Subscribe on connect."""
    if rc == 0:
        print("✅ Connected to MQTT for ingestion (IoT Core).")
        devices = ["refrigerator", "oven", "microwave"]
        for device in devices:
            topic = MQTT_PREFIX + device
            client.subscribe(topic)
            print(f"📥 Subscribed to {topic}")
    else:
        print(f"❌ MQTT connect failed: {rc}")

def on_message(client, userdata, msg):
    """Handle incoming message: Parse JSON, insert to DB."""
    try:
        data = json.loads(msg.payload.decode())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sensor_data (timestamp, device, temperature_C, CO_ppm, CO2_ppm, power_W)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data['timestamp'],
            data['device'],
            data['temperature_C'],
            data['CO_ppm'],
            data['CO2_ppm'],
            data['power_W']
        ))
        conn.commit()
        conn.close()
        print(f"💾 Ingested: {data['device']} at {data['timestamp'][:19]} ({data['temperature_C']}°C)")
    except Exception as e:
        print(f"❌ Ingestion error: {e}")

def consume_and_ingest():
    init_db()
    client = mqtt.Client(client_id='smart-kitchen-ingester')  # Unique client ID
    
    # TLS for IoT Core (skip if local)
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
    client.loop_forever()  # Blocks indefinitely

if __name__ == "__main__":
    consume_and_ingest()
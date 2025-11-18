import os
import json
import sqlite3
import paho.mqtt.client as mqtt
from pathlib import Path
import ssl  # For IoT Core TLS

DB_PATH = os.getenv('DB_PATH', '/app/kitchen.db')
MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
CA_PATH = os.getenv('CA_PATH', '')
CERT_PATH = os.getenv('CERT_PATH', '')
KEY_PATH = os.getenv('KEY_PATH', '')
MQTT_PREFIX = 'smart_kitchen/'
TENANT_ID = os.getenv('TENANT_ID', 'demo')

def init_db():
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
            power_W REAL,
            tenant_id TEXT DEMO 'demo'
        )
    """)
    # Backfill tenant_id if column missing (for legacy)
    try:
        cursor.execute("ALTER TABLE sensor_data ADD COLUMN tenant_id TEXT DEMO 'demo'")
    except sqlite3.OperationalError:
        pass  # Column exists
    cursor.execute("UPDATE sensor_data SET tenant_id = 'demo' WHERE tenant_id IS NULL")
    conn.commit()
    conn.close()
    print("✅ DB initialized with tenant_id support.")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected for ingestion.")
        devices = ["refrigerator", "oven", "microwave"]
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
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sensor_data (timestamp, device, temperature_C, CO_ppm, CO2_ppm, power_W, tenant_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data['timestamp'],
            data['device'],
            data['temperature_C'],
            data['CO_ppm'],
            data['CO2_ppm'],
            data['power_W'],
            data['tenant_id']
        ))
        conn.commit()
        conn.close()
        print(f"💾 Ingested ({TENANT_ID}): {data['device']} at {data['timestamp'][:19]} ({data['temperature_C']}°C)")
    except Exception as e:
        print(f"❌ Ingestion error: {e}")

def consume_and_ingest():
    init_db()
    client = mqtt.Client(client_id=f'smart-kitchen-ingester-{TENANT_ID}')
    
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
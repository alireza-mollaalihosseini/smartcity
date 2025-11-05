import os
import json
import sqlite3
import paho.mqtt.client as mqtt
from pathlib import Path

# Compute project root: Up one level from script dir
project_root = Path(__file__).parent.parent.absolute()
# DB_PATH = project_root / "kitchen.db"  # Single DB in root
DB_PATH = "/app/kitchen.db"
# MQTT_BROKER = 'localhost'
MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = 1883
MQTT_PREFIX = 'smart_kitchen/'
# DB_PATH = os.path.join(base_dir, "data_pipeline", "kitchen.db") # '/data_pipeline/kitchen.db'


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
        print("✅ Connected to MQTT for ingestion.")
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
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()  # Blocks indefinitely

if __name__ == "__main__":
    consume_and_ingest()
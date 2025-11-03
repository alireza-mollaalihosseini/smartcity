import json
import sqlite3
from kafka import KafkaConsumer
from datetime import datetime
import pandas as pd  # For any batch inserts if needed

KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC_PREFIX = 'smart_kitchen_'
DB_PATH = 'smart_kitchen_kafka.db'  # Adjust to your DB path

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

def consume_and_ingest():
    """Consume from Kafka and insert to SQLite."""
    init_db()
    devices = ["refrigerator", "oven", "microwave"]
    consumer = KafkaConsumer(
        *[TOPIC_PREFIX + device for device in devices],
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',  # Start from new messages
        enable_auto_commit=True,
        group_id='kitchen-ingestion-group'
    )
    
    print("📥 Starting ingestion from Kafka to SQLite...")
    conn = sqlite3.connect(DB_PATH)
    
    try:
        for message in consumer:
            data = message.value
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
            print(f"💾 Ingested: {data['device']} at {data['timestamp'][:19]}")
    except KeyboardInterrupt:
        print("🛑 Ingestion stopped.")
    finally:
        conn.close()
        consumer.close()

if __name__ == "__main__":
    consume_and_ingest()
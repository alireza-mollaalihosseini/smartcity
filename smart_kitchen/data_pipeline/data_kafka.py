import os
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from kafka import KafkaProducer
from threading import Thread
import argparse

# Kafka config (local setup)
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC_PREFIX = 'smart_kitchen_'

def create_producer():
    """Initialize Kafka producer with JSON serializer."""
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        retries=3,  # Fault tolerance
        acks='all'  # Durability
    )

def generate_sample_data(device_name):
    """Generate a single realistic sample (your logic, but per-timestamp)."""
    if device_name == "refrigerator":
        temp = np.random.normal(4, 0.5)
        co = np.random.normal(2, 0.2)
        co2 = np.random.normal(400, 20)
        power = np.random.normal(120, 5)
    elif device_name == "oven":
        temp = np.random.normal(180, 10)
        co = np.random.normal(10, 1)
        co2 = np.random.normal(600, 30)
        power = np.random.normal(2000, 50)
    elif device_name == "microwave":
        temp = np.random.normal(90, 5)
        co = np.random.normal(5, 0.5)
        co2 = np.random.normal(450, 25)
        power = np.random.normal(800, 20)
    else:
        raise ValueError("Unknown device name")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "device": device_name,
        "temperature_C": round(temp, 2),
        "CO_ppm": round(co, 2),
        "CO2_ppm": round(co2, 2),
        "power_W": round(power, 2)
    }

def simulate_device_stream(device_name, freq_seconds=10, duration_minutes=None):
    """Stream data for one device in real-time to Kafka."""
    producer = create_producer()
    topic = TOPIC_PREFIX + device_name
    print(f"🚀 Starting {device_name} stream to topic '{topic}' (every {freq_seconds}s)...")
    
    start_time = datetime.now()
    sample_count = 0
    end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes else None
    
    try:
        while True:
            if end_time and datetime.now() > end_time:
                print(f"⏹️ {device_name} stream ended after {duration_minutes} min.")
                break
            
            sample = generate_sample_data(device_name)
            producer.send(topic, value=sample)
            sample_count += 1
            print(f"📤 Sent sample #{sample_count} for {device_name}: {sample['temperature_C']}°C, {sample['power_W']}W")
            
            time.sleep(freq_seconds)  # Simulate real-time interval
    except KeyboardInterrupt:
        print(f"🛑 Interrupted {device_name} stream.")
    finally:
        producer.flush()
        producer.close()

def simulate_all_devices(freq_seconds=10, duration_minutes=None):
    """Run streams for all devices in parallel threads."""
    devices = ["refrigerator", "oven", "microwave"]
    threads = []
    
    for device in devices:
        t = Thread(target=simulate_device_stream, args=(device, freq_seconds, duration_minutes))
        t.daemon = True
        t.start()
        threads.append(t)
    
    try:
        # Wait for all threads (or duration)
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("🛑 Stopping all streams.")

if __name__ == "__main__":
    # # Run for 5 min as example; set to None for indefinite
    # simulate_all_devices(freq_seconds=10, duration_minutes=5)

    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", default=5, type=int)  # minutes
    args = parser.parse_args()
    simulate_all_devices(duration_minutes=args.duration if args.duration != "indefinite" else None)
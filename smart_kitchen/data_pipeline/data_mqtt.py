import os
import json
import time
import argparse
import numpy as np
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt

# MQTT config (local)
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_PREFIX = 'smart_kitchen/'
QOS = 1  # At-least-once delivery

def on_connect(client, userdata, flags, rc):
    """Callback on connect."""
    if rc == 0:
        print("✅ Connected to MQTT broker.")
    else:
        print(f"❌ MQTT connect failed: {rc}")

def generate_sample_data(device_name):
    """Generate a single realistic sample (unchanged)."""
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

def simulate_device_stream(client, device_name, freq_seconds=10, duration_minutes=None):
    """Stream data for one device to MQTT."""
    topic = MQTT_PREFIX + device_name
    client.subscribe(topic)  # Optional: Echo back for logging
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
            payload = json.dumps(sample)
            client.publish(topic, payload, qos=QOS)
            sample_count += 1
            print(f"📤 Sent sample #{sample_count} for {device_name}: {sample['temperature_C']}°C, {sample['power_W']}W")
            
            time.sleep(freq_seconds)
    except KeyboardInterrupt:
        print(f"🛑 Interrupted {device_name} stream.")

def simulate_all_devices(freq_seconds=10, duration_minutes=None):
    """Run streams for all devices in parallel threads."""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()  # Non-blocking loop
    
    devices = ["refrigerator", "oven", "microwave"]
    from threading import Thread
    
    threads = []
    for device in devices:
        t = Thread(target=simulate_device_stream, args=(client, device, freq_seconds, duration_minutes))
        t.daemon = True
        t.start()
        threads.append(t)
    
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("🛑 Stopping all streams.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", default=None, type=str)  # e.g., "5" or "indefinite"
    args = parser.parse_args()
    duration_min = None if args.duration == "indefinite" else (int(args.duration) if args.duration else 5)
    simulate_all_devices(duration_minutes=duration_min)
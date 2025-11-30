# data.py (Modified for Smart Home Property Insurance Demo)

import os
import json
import time
import argparse
import numpy as np
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import ssl  # For IoT Core TLS

# IoT Core config
MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
CA_PATH = os.getenv('CA_PATH', '')
CERT_PATH = os.getenv('CERT_PATH', '')
KEY_PATH = os.getenv('KEY_PATH', '')
MQTT_PREFIX = 'smart_home/'  # Updated for smart home
TENANT_ID = os.getenv('TENANT_ID', 'demo')
QOS = 1

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected for tenant {TENANT_ID}.")
    else:
        print(f"❌ Connect failed: {rc}")

def generate_sample_data(device_name):
    timestamp = datetime.now().isoformat()
    base_data = {
        "timestamp": timestamp,
        "device": device_name,
        "tenant_id": TENANT_ID
    }
    
    if device_name == "smoke_detector":
        smoke_ppm = np.random.exponential(5)  # Low normal, occasional spikes for demo
        if np.random.random() < 0.01:  # Rare alarm simulation
            smoke_ppm = np.random.uniform(60, 100)
        alarm = smoke_ppm > 50
        readings = {
            "smoke_ppm": round(smoke_ppm, 2),
            "alarm": alarm
        }
    elif device_name == "water_sensor":
        moisture_percent = np.random.normal(10, 5)  # Mostly dry
        if np.random.random() < 0.005:  # Rare leak
            moisture_percent = np.random.uniform(70, 100)
        leak_detected = moisture_percent > 50
        readings = {
            "moisture_percent": round(moisture_percent, 2),
            "leak_detected": leak_detected
        }
    elif device_name == "door_sensor":
        state = "closed" if np.random.random() < 0.9 else "open"  # Mostly closed
        last_change = (datetime.now() - timedelta(minutes=np.random.uniform(0, 60))).isoformat()
        readings = {
            "state": state,
            "last_change": last_change
        }
    elif device_name == "temperature_sensor":
        temp = np.random.normal(21, 3)  # Room temp
        if np.random.random() < 0.02:  # Rare extreme for demo (e.g., heating failure)
            temp = np.random.uniform(-5, 5)  # Freezing risk
        readings = {
            "temp_C": round(temp, 2)
        }
    elif device_name == "humidity_sensor":
        humidity = np.random.normal(50, 10)  # Comfortable range
        readings = {
            "humidity_percent": round(humidity, 2)
        }
    elif device_name == "motion_detector":
        motion_detected = np.random.random() < 0.1  # Occasional motion
        last_detected = timestamp if motion_detected else None
        readings = {
            "motion_detected": motion_detected,
            "last_detected": last_detected
        }
    else:
        raise ValueError("Unknown device")
    
    return {**base_data, "readings": readings}

def simulate_device_stream(client, device_name, freq_seconds=10, duration_minutes=None):
    topic = f"{TENANT_ID}/{MQTT_PREFIX}{device_name}"
    print(f"🚀 Starting {device_name} stream to '{topic}' for {TENANT_ID}...")
    
    start_time = datetime.now()
    sample_count = 0
    end_time = start_time + timedelta(minutes=duration_minutes) if duration_minutes else None
    
    try:
        while True:
            if end_time and datetime.now() > end_time:
                print(f"⏹️ {device_name} ended after {duration_minutes} min.")
                break
            
            sample = generate_sample_data(device_name)
            payload = json.dumps(sample)
            client.publish(topic, payload, qos=QOS)
            sample_count += 1
            # Print a summary based on device
            if device_name == "smoke_detector":
                print(f"📤 #{sample_count} for {device_name} (Tenant: {TENANT_ID}): {sample['readings']['smoke_ppm']}ppm, Alarm: {sample['readings']['alarm']}")
            elif device_name == "water_sensor":
                print(f"📤 #{sample_count} for {device_name} (Tenant: {TENANT_ID}): {sample['readings']['moisture_percent']}% moisture, Leak: {sample['readings']['leak_detected']}")
            else:
                print(f"📤 #{sample_count} for {device_name} (Tenant: {TENANT_ID}): {sample['readings']}")
            
            time.sleep(freq_seconds)
    except KeyboardInterrupt:
        print(f"🛑 Interrupted {device_name}.")

def simulate_all_devices(freq_seconds=10, duration_minutes=None):
    client = mqtt.Client(client_id=f'smart-home-simulator-{TENANT_ID}')
    print(f"🔍 In background: MQTT_ENDPOINT={os.getenv('MQTT_ENDPOINT')}, TENANT_ID={os.getenv('TENANT_ID')}")
    client.on_connect = on_connect

    # Debug print
    print(f"🔍 Connecting to {MQTT_ENDPOINT}:{MQTT_PORT} (Tenant: {TENANT_ID}) with certs: CA={CA_PATH}, CERT={CERT_PATH}, KEY={KEY_PATH}")
    
    if MQTT_ENDPOINT != 'localhost':
        client.tls_set(
            ca_certs=CA_PATH,
            certfile=CERT_PATH,
            keyfile=KEY_PATH,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )

    try:
        client.connect(MQTT_ENDPOINT, MQTT_PORT, 60)
        print("✅ Connect attempted—waiting for on_connect callback.")
    except ConnectionRefusedError as e:
        print(f"❌ Connect refused: {e}. Check certs/policy/network.")
        return  # Skip threads
    
    client.loop_start()
    
    from threading import Thread
    devices = ["smoke_detector", "water_sensor", "door_sensor", "temperature_sensor", "humidity_sensor", "motion_detector"]
    threads = [Thread(target=simulate_device_stream, args=(client, device, freq_seconds, duration_minutes)) for device in devices]
    for t in threads:
        t.daemon = True
        t.start()
    
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print(f"🛑 Stopping streams for {TENANT_ID}.")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", default="5", type=str, help="Duration in min or 'indefinite'")
    args = parser.parse_args()
    duration_min = None if args.duration == "indefinite" else int(args.duration)
    simulate_all_devices(duration_minutes=duration_min)
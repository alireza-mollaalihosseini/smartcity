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
MQTT_PREFIX = 'smart_kitchen/'
TENANT_ID = os.getenv('TENANT_ID', 'demo')
QOS = 1

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected for tenant {TENANT_ID}.")
    else:
        print(f"❌ Connect failed: {rc}")

def generate_sample_data(device_name):
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
        raise ValueError("Unknown device")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "device": device_name,
        "temperature_C": round(temp, 2),
        "CO_ppm": round(co, 2),
        "CO2_ppm": round(co2, 2),
        "power_W": round(power, 2),
        "tenant_id": TENANT_ID
    }

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
            print(f"📤 #{sample_count} for {device_name} (Tenant: {TENANT_ID}): {sample['temperature_C']}°C, {sample['power_W']}W")
            
            time.sleep(freq_seconds)
    except KeyboardInterrupt:
        print(f"🛑 Interrupted {device_name}.")

def simulate_all_devices(freq_seconds=10, duration_minutes=None):
    client = mqtt.Client(client_id=f'smart-kitchen-simulator-{TENANT_ID}')
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
    
    # client.connect(MQTT_ENDPOINT, MQTT_PORT, 60)
    client.loop_start()
    
    from threading import Thread
    devices = ["refrigerator", "oven", "microwave"]
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
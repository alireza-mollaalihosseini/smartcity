import os
import json
import paho.mqtt.client as mqtt
import ssl  # For IoT Core TLS
from datetime import datetime

# IoT Core config
MQTT_ENDPOINT = os.getenv('MQTT_ENDPOINT', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', 8883 if MQTT_ENDPOINT != 'localhost' else 1883))
CA_PATH = os.getenv('CA_PATH', '')
CERT_PATH = os.getenv('CERT_PATH', '')
KEY_PATH = os.getenv('KEY_PATH', '')
ALERT_TOPIC = 'smart_kitchen/alerts'
ALERT_LOG = os.getenv('ALERTS_PATH', '/app/alerts') + '/alert_log.txt'

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT for alerts (IoT Core).")
        client.subscribe(ALERT_TOPIC)
    else:
        print(f"❌ MQTT connect failed: {rc}")

def on_message(client, userdata, msg):
    if msg.topic == ALERT_TOPIC:
        try:
            alert = json.loads(msg.payload.decode())
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] {alert.get('device', 'Unknown')}: {alert.get('message', 'No message')}\n"
            with open(ALERT_LOG, 'a') as f:
                f.write(log_entry)
            print(f"🔔 Alert logged: {log_entry.strip()}")
            # Optional: Pub back confirmation or webhook
        except Exception as e:
            print(f"❌ Alert processing error: {e}")

if __name__ == "__main__":
    client = mqtt.Client(client_id='smart-kitchen-alerts')
    
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
    client.loop_forever()
import json
import paho.mqtt.client as mqtt

MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_PREFIX = 'smart_kitchen/'

def send_alert(device, metric, value):
    """Placeholder: Customize for email/Slack/etc."""
    print(f"🚨 ALERT: {device} - {metric} spiked to {value}!")

def check_and_alert(data):
    """Threshold checks."""
    if data['CO_ppm'] > 8:
        send_alert(data['device'], 'CO', data['CO_ppm'])
    if data['temperature_C'] > 200:
        send_alert(data['device'], 'Temp', data['temperature_C'])

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT for alerts.")
        devices = ["refrigerator", "oven", "microwave"]
        for device in devices:
            topic = MQTT_PREFIX + device
            client.subscribe(topic)
    else:
        print(f"❌ MQTT connect failed: {rc}")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        check_and_alert(data)
    except Exception as e:
        print(f"❌ Alert processing error: {e}")

def run_alert_consumer():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    run_alert_consumer()
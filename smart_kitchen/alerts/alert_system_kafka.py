import json
from kafka import KafkaConsumer
import smtplib  # Or use Twilio/Slack for real alerts

KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC_PREFIX = 'smart_kitchen_'

def send_alert(device, metric, value):
    """Placeholder: Send email/Slack."""
    print(f"🚨 ALERT: {device} - {metric} spiked to {value}!")  # Replace with real notifier

def check_and_alert(data):
    """Simple threshold checks."""
    if data['CO_ppm'] > 8:
        send_alert(data['device'], 'CO', data['CO_ppm'])
    if data['temperature_C'] > 200:  # e.g., oven fire risk
        send_alert(data['device'], 'Temp', data['temperature_C'])

def run_alert_consumer():
    devices = ["refrigerator", "oven", "microwave"]
    consumer = KafkaConsumer(
        *[TOPIC_PREFIX + device for device in devices],
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        group_id='kitchen-alerts-group'
    )
    
    print("🔔 Starting real-time alerts...")
    try:
        for message in consumer:
            data = message.value
            check_and_alert(data)
    except KeyboardInterrupt:
        print("🛑 Alerts stopped.")
    finally:
        consumer.close()

if __name__ == "__main__":
    run_alert_consumer()
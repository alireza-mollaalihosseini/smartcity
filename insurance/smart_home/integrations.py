import os
import json
import paho.mqtt.client as mqtt
import requests  # For policyholder app API calls
from datetime import datetime

# Insurance Portal Bridge Config (customer-specific; set via env or per-tenant)
INSURANCE_BROKER = os.getenv('INSURANCE_BROKER', 'insurance-portal.local')  # e.g., customer's insurance CRM IP
INSURANCE_PORT = int(os.getenv('INSURANCE_PORT', 1883))
INSURANCE_USER = os.getenv('INSURANCE_USER', '')  # Insurance MQTT user
INSURANCE_PASS = os.getenv('INSURANCE_PASS', '')  # Insurance MQTT pass

# Policyholder App Config (mock FCM or Twilio stub)
APP_CLIENT_ID = os.getenv('APP_CLIENT_ID', '')  # From app provider
APP_SECRET = os.getenv('APP_SECRET', '')  # Client secret
APP_ACCESS_TOKEN = os.getenv('APP_TOKEN', '')  # From OAuth flow (stub for now)

def bridge_to_insurance_portal(data, tenant_id):
    """
    Bridge sensor data or alert to Insurance Portal MQTT.
    Usage: Call on new data/alert, e.g., from alert_system.py.
    """
    if not INSURANCE_BROKER or INSURANCE_BROKER == 'insurance-portal.local':  # Skip if not configured
        print("Insurance integration: Config missing (set INSURANCE_BROKER env).")
        return

    client = mqtt.Client(client_id=f'sh-insurance-bridge-{tenant_id}-{datetime.now().timestamp()}')
    if INSURANCE_USER and INSURANCE_PASS:
        client.username_pw_set(INSURANCE_USER, INSURANCE_PASS)
    
    client.connect(INSURANCE_BROKER, INSURANCE_PORT, 60)
    
    # Insurance Discovery Topic (auto-creates entities in portal)
    discovery_topic = f"homeassistant/sensor/sh_{tenant_id}_{data['device']}/config"
    # Adjust unit and template based on device
    if data['device'] == 'smoke_detector':
        unit = "ppm"
        template = "{{ value_json.readings.smoke_ppm }}"
    elif data['device'] == 'water_sensor':
        unit = "%"
        template = "{{ value_json.readings.moisture_percent }}"
    else:
        unit = ""
        template = "{{ value_json.readings }}"
    
    discovery_payload = {
        "name": f"Smart Home {data['device'].replace('_', ' ').title()} ({tenant_id})",
        "state_topic": f"homeassistant/sensor/sh_{tenant_id}_{data['device']}/state",
        "unit_of_measurement": unit,
        "value_template": template,
        "device": {"identifiers": [f"sh-{tenant_id}-{data['device']}"]}
    }
    client.publish(discovery_topic, json.dumps(discovery_payload), qos=0, retain=True)
    
    # State Topic (live data)
    state_topic = f"homeassistant/sensor/sh_{tenant_id}_{data['device']}/state"
    state_payload = json.dumps(data)
    client.publish(state_topic, state_payload, qos=1, retain=False)
    
    client.disconnect()
    print(f"✅ Bridged to Insurance Portal (Tenant: {tenant_id}): {data['device']} data sent to {state_topic}")

def send_to_policyholder_app(alert_msg, device_id, tenant_id):
    """
    Send alert to Policyholder Mobile App via mock FCM API.
    Usage: Call on anomaly, e.g., from alert_system.py.
    Setup: App provider > Enable FCM > Create OAuth client > Get token.
    """
    if not APP_ACCESS_TOKEN:
        print("Policyholder app integration: Auth required (set APP_TOKEN env via OAuth). Stub alert logged.")
        # Stub: Log instead of send
        with open(os.getenv('ALERTS_PATH', '/app/alerts') + f'/{tenant_id}_app_stubs.txt', 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {alert_msg} for {device_id}\n")
        return

    # Mock FCM Endpoint (replace with real app API)
    app_id = os.getenv('APP_ENTERPRISE_ID', 'apps/project-default')  # From app setup
    device_path = f"{app_id}/devices/{device_id}"  # e.g., 'projects/123/devices/smoke-detector-1'
    
    headers = {
        'Authorization': f'Bearer {APP_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "command": "fcm.devices.commands.Notify",
        "params": {
            "notificationMessage": alert_msg
        }
    }
    
    response = requests.post(f"https://fcm.googleapis.com/v1/{device_path}:send",  # Mocked to FCM-like
                             json=payload, headers=headers)
    if response.status_code == 200:
        print(f"✅ Sent to Policyholder App (Tenant: {tenant_id}): {alert_msg} for {device_id}")
    else:
        print(f"❌ App API error: {response.status_code} - {response.text}")

# Example Usage (for testing: python integrations.py)
if __name__ == "__main__":
    sample_data = {
        "timestamp": datetime.now().isoformat(),
        "device": "smoke_detector",
        "readings": {
            "smoke_ppm": 65.2,
            "alarm": True
        }
    }
    sample_alert = "Smoke detected - potential fire risk, review coverage!"
    
    bridge_to_insurance_portal(sample_data, 'demo')
    send_to_policyholder_app(sample_alert, 'smoke-detector-1', 'demo')
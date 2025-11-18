import os
import json
import paho.mqtt.client as mqtt
import requests  # For Google API calls
from datetime import datetime

# HA Bridge Config (customer-specific; set via env or per-tenant)
HA_BROKER = os.getenv('HA_BROKER', 'homeassistant.local')  # e.g., customer's HA IP
HA_PORT = int(os.getenv('HA_PORT', 1883))
HA_USER = os.getenv('HA_USER', '')  # HA MQTT user
HA_PASS = os.getenv('HA_PASS', '')  # HA MQTT pass

# Google Home Config (SDM API stub)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '')  # From Google Cloud Console
GOOGLE_SECRET = os.getenv('GOOGLE_SECRET', '')  # Client secret
GOOGLE_ACCESS_TOKEN = os.getenv('GOOGLE_TOKEN', '')  # From OAuth flow (stub for now)

def bridge_to_ha(data, tenant_id):
    """
    Bridge sensor data or alert to Home Assistant MQTT.
    Usage: Call on new data/alert, e.g., from alert_system_demo.py.
    """
    if not HA_BROKER or HA_BROKER == 'homeassistant.local':  # Skip if not configured
        print("HA integration: Config missing (set HA_BROKER env).")
        return

    client = mqtt.Client(client_id=f'sk-ha-bridge-{tenant_id}-{datetime.now().timestamp()}')
    if HA_USER and HA_PASS:
        client.username_pw_set(HA_USER, HA_PASS)
    
    client.connect(HA_BROKER, HA_PORT, 60)
    
    # HA Discovery Topic (auto-creates entities in HA)
    discovery_topic = f"homeassistant/sensor/sk_{tenant_id}_{data['device']}/config"
    discovery_payload = {
        "name": f"Smart Kitchen {data['device'].title()} ({tenant_id})",
        "state_topic": f"homeassistant/sensor/sk_{tenant_id}_{data['device']}/state",
        "unit_of_measurement": "°C" if "temp" in data else "W",
        "value_template": "{{ value_json.temperature_C }}" if "temp" in data else "{{ value_json.power_W }}",
        "device": {"identifiers": [f"sk-{tenant_id}-{data['device']}"]}
    }
    client.publish(discovery_topic, json.dumps(discovery_payload), qos=0, retain=True)
    
    # State Topic (live data)
    state_topic = f"homeassistant/sensor/sk_{tenant_id}_{data['device']}/state"
    state_payload = json.dumps(data)
    client.publish(state_topic, state_payload, qos=1, retain=False)
    
    client.disconnect()
    print(f"✅ Bridged to HA (Tenant: {tenant_id}): {data['device']} data sent to {state_topic}")

def send_to_google_home(alert_msg, device_id, tenant_id):
    """
    Send alert to Google Home/Nest via SDM API.
    Usage: Call on anomaly, e.g., from alert_system_demo.py.
    Setup: Google Cloud > Enable SDM API > Create OAuth client > Get token.
    """
    if not GOOGLE_ACCESS_TOKEN:
        print("Google integration: Auth required (set GOOGLE_TOKEN env via OAuth). Stub alert logged.")
        # Stub: Log instead of send
        with open(os.getenv('ALERTS_PATH', '/app/alerts') + f'/{tenant_id}_google_stubs.txt', 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {alert_msg} for {device_id}\n")
        return

    # SDM API Endpoint (replace 'project-id' with yours)
    enterprise_id = os.getenv('GOOGLE_ENTERPRISE_ID', 'enterprises/project-default')  # From SDM setup
    device_path = f"{enterprise_id}/devices/{device_id}"  # e.g., 'projects/123/devices/oven-1'
    
    headers = {
        'Authorization': f'Bearer {GOOGLE_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "command": "sdm.devices.commands.Announce",
        "params": {
            "announceMessage": alert_msg
        }
    }
    
    response = requests.post(f"https://smartdevicemanagement.googleapis.com/v1/{device_path}:executeCommand", 
                             json=payload, headers=headers)
    if response.status_code == 200:
        print(f"✅ Sent to Google Home (Tenant: {tenant_id}): {alert_msg} for {device_id}")
    else:
        print(f"❌ Google API error: {response.status_code} - {response.text}")

# Example Usage (for testing: python integrations.py)
if __name__ == "__main__":
    sample_data = {
        "timestamp": datetime.now().isoformat(),
        "device": "oven",
        "temperature_C": 220.5,
        "power_W": 2100
    }
    sample_alert = "High temperature detected—check oven!"
    
    bridge_to_ha(sample_data, 'demo')
    send_to_google_home(sample_alert, 'oven-1', 'demo')
# Smart Home – Property Insurance Demo

The [smart kitchen](../smart_kitchen) backend adapted to a property-insurance scenario. Simulated home
sensors report the events an insurer cares about (fire, water damage, break-in, climate), so that a
policyholder is alerted early and an insurer could act before a claim.

| Folder | Contents |
|---|---|
| [`smart_home/`](smart_home) | Python backend: simulator, ingestion, alerts, Streamlit dashboard, Flask REST API (JWT), Nginx, Docker Compose |
| [`flutter_smart_home/`](flutter_smart_home) | Flutter app for policyholders (login, devices, live charts, alerts) |

## Sensors

| Device | Readings | Simulated events |
|---|---|---|
| `smoke_detector` | smoke (ppm), alarm flag | rare smoke spikes that trigger the alarm |
| `water_sensor` | moisture (%), leak flag | rare leaks |
| `door_sensor` | open/closed, time of last change | door occasionally open |
| `motion_detector` | motion flag, time last detected | occasional motion |
| `temperature_sensor` | °C | rare near-freezing readings (heating failure) |
| `humidity_sensor` | % RH | normal indoor range |

Readings are published over MQTT (local broker or AWS IoT Core, prefix `smart_home/`), stored in SQLite
and checked by the alert engine. `src/predictive_maintenance/train_predictor.py` contains a prototype
logistic-regression *risk* classifier. Its labels are derived from threshold rules, and it is not yet
called by the pipeline.

## Running

The setup mirrors the smart kitchen: see [smart_kitchen/README.md](../smart_kitchen/README.md#running-it).

```bash
cd insurance/smart_home
pip install -r requirements.txt
docker run -d -p 1883:1883 -v "$PWD/../../smart_kitchen/config:/mosquitto/config" eclipse-mosquitto:2.0   # local broker
python main.py                              # simulator, ingestion, alerts and the REST API on :8080
streamlit run dashboard/dashboard_app.py    # second terminal
```

For the Docker Compose / AWS IoT Core setup, put the device certificates in `certs/` and create a `.env`
file as described in the smart kitchen README, then run `docker compose up --build`.

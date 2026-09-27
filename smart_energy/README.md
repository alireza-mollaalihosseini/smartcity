# Smart Energy

Simulation and analysis of a smart-meter fleet: 200 meters (70% residential, 20% commercial, 10%
industrial) report consumption, voltage and grid frequency every 5 minutes. The data is loaded into
PostgreSQL, where a worker flags anomalies and trains a short-term consumption forecast.

| Step | File | What it does |
|---|---|---|
| Simulate | `data_pipeline/simulate_meters.py` | Daily load curve (sinusoid) + noise per meter type; injects spikes and outages in about 0.5% of samples; also writes a simple weather series. Output: `data_pipeline/simulated_energy/{meters,weather}.csv` |
| Ingest | `data_pipeline/ingest_to_db.py` | Creates the `energy_readings` table (with time and meter indexes) and bulk-loads the CSV in chunks via SQLAlchemy |
| Anomalies | `src/anomaly_detection_energy.py` | Isolation Forest (1% contamination) on consumption, voltage and frequency over the last 24 h; writes hits to `energy_anomalies` |
| Forecast | `src/forecasting.py` | Random Forest regressor predicting each meter's next reading from a rolling mean/std window plus voltage and frequency; saves `models/energy_forecast.pkl` |

## Running locally

Run these from the repository root (the default paths are relative to it). You need a PostgreSQL
instance and `ENERGY_DB_URL` pointing at it:

```bash
pip install -r smart_energy/requirements.txt
export ENERGY_DB_URL=postgresql://<user>:<password>@localhost:5432/smartcity

python smart_energy/data_pipeline/simulate_meters.py
python smart_energy/data_pipeline/ingest_to_db.py
python smart_energy/src/anomaly_detection_energy.py
python smart_energy/src/forecasting.py
```

## Kubernetes

[`../k8s/smart-energy/`](../k8s/smart-energy) runs the simulator as a CronJob (every 5 minutes) and the
anomaly and forecast jobs in a worker Deployment, against the PostgreSQL service in the
`infrastructure` namespace. The simulator currently writes CSV files only, so run `ingest_to_db.py` to
load them into the database.

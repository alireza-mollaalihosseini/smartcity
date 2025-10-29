# smart_energy/data_pipeline/ingest_to_db.py
import os
import pandas as pd
from sqlalchemy import create_engine, text
import argparse

DB_URL = os.environ.get("ENERGY_DB_URL", "postgresql://admin:admin123@postgres.infrastructure.svc.cluster.local:5432/smartcity")

def ensure_table(engine):
    # simple table; in production convert to hypertable (Timescale)
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS energy_readings (
            timestamp TIMESTAMP NOT NULL,
            meter_id TEXT NOT NULL,
            meter_type TEXT,
            consumption_kwh DOUBLE PRECISION,
            voltage DOUBLE PRECISION,
            frequency_hz DOUBLE PRECISION
        );
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_energy_time ON energy_readings (timestamp);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_meter_id ON energy_readings (meter_id);"))

def ingest(csv_path, db_url=DB_URL):
    engine = create_engine(db_url, pool_size=5, max_overflow=10)
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    # write in chunks
    df.to_sql("energy_readings", engine, if_exists="append", index=False, method="multi", chunksize=5000)
    print(f"Ingested {len(df)} rows to {db_url}")

if __name__ == "__main__":
    import glob
    engine = create_engine(DB_URL)
    ensure_table(engine)
    csv = "smart_energy/data_pipeline/simulated_energy/meters.csv"
    ingest(csv)

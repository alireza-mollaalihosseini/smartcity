import os
import sqlite3
import pandas as pd

def create_database(db_path="smart_kitchen.db"):
    """Create an SQLite database if it doesn’t exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (
        device TEXT,
        timestamp TEXT,
        temperature_C REAL,
        CO_ppm REAL,
        CO2_ppm REAL,
        power_W REAL
    )
    """)
    conn.commit()
    conn.close()
    print(f"✅ Database created or verified at {db_path}")


def upload_csv_to_db(csv_path, db_path="smart_kitchen.db"):
    """Read each device CSV and append to the database."""
    conn = sqlite3.connect(db_path)
    df = pd.read_csv(csv_path)
    device = os.path.basename(csv_path).split(".")[0]
    df["device"] = device
    df.to_sql("sensor_data", conn, if_exists="append", index=False)
    conn.close()
    print(f"📤 Uploaded {device} data to database.")


def upload_all_data(data_dir="simulated_data"):
    """Upload all .csv files in the simulated data directory."""
    create_database()
    for file in os.listdir(data_dir):
        if file.endswith(".csv"):
            upload_csv_to_db(os.path.join(data_dir, file))


if __name__ == "__main__":
    upload_all_data()

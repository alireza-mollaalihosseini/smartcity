from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import os
from datetime import datetime


# ======================================================
# Configuration
# ======================================================

DATA_DIR = "../../data/raw"
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(title="Smart Kitchen IoT Data Ingestion API",
              description="Receives IoT sensor data from kitchen devices.",
              version="1.0")


# ======================================================
# Data Model (Validation)
# ======================================================

class SensorReading(BaseModel):
    timestamp: str
    temperature: float
    co: float
    co2: float
    power: float
    device: str


class DeviceData(BaseModel):
    device_id: str
    readings: List[SensorReading]


# ======================================================
# Helper Function
# ======================================================

def save_to_csv(device_name: str, readings: List[Dict[str, Any]]):
    """Append received data to a CSV file."""
    df = pd.DataFrame(readings)
    filename = os.path.join(DATA_DIR, f"{device_name}_data_received.csv")
    file_exists = os.path.isfile(filename)
    df.to_csv(filename, mode="a", header=not file_exists, index=False)
    print(f"[✓] Saved {len(df)} new rows to {filename}")


# ======================================================
# API Endpoints
# ======================================================

@app.get("/")
def root():
    return {"status": "online", "message": "Smart Kitchen Ingestion Server is running 🚀"}


@app.post("/upload_data")
async def upload_data(payload: DeviceData):
    try:
        readings = [reading.dict() for reading in payload.readings]
        save_to_csv(payload.device_id, readings)
        return JSONResponse(content={"status": "success", "rows_received": len(readings)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ======================================================
# Run the server
# ======================================================

if __name__ == "__main__":
    import uvicorn
    print("🔧 Starting Smart Kitchen Ingestion Server...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI, Request
import pandas as pd

app = FastAPI()

@app.post("/upload_data")
async def upload_data(request: Request):
    payload = await request.json()
    df = pd.DataFrame(payload["data"])
    df.to_csv("data/raw/sensor_data.csv", mode="a", header=False, index=False)
    return {"status": "success", "received": len(df)}

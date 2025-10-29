FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
CMD ["python", "data_pipeline/simulate_meters.py"]
# NOTE: container runnable mode: you may run different entrypoints (simulator vs worker) with args

# Kubernetes manifests

Manifests for running the platform on a local Minikube cluster.

```
k8s/
├── base/
│   ├── namespaces.yaml      # infrastructure, smart-kitchen, smart-energy, smart-trains
│   ├── postgres.yaml        # PostgreSQL 15 + PersistentVolume/Claim
│   ├── minio.yaml           # S3-compatible object storage
│   └── rabbitmq.yaml        # message broker (AMQP + management UI)
├── smart-kitchen/
│   ├── deployment.yaml      # Streamlit app (image smart-kitchen:latest)
│   └── service.yaml         # NodePort 30001 -> 8501
└── smart-energy/
    ├── cronjob-simulator.yaml   # meter simulator every 5 minutes
    └── deployment-energy.yaml   # worker: anomaly detection + forecast every 5 minutes
```

## Usage

```bash
minikube start --driver=docker

# build the images inside Minikube's Docker daemon
eval $(minikube docker-env)
docker build -t smart-kitchen:latest ../smart_kitchen
docker build -t smartcity-energy-simulator:0.1 -t smartcity-energy-worker:0.1 ../smart_energy

kubectl apply -f base/namespaces.yaml
kubectl apply -f base/
kubectl apply -f smart-kitchen/ -f smart-energy/

minikube service smart-kitchen-service -n smart-kitchen   # open the dashboard
```

The database and MinIO credentials in `base/` are local development defaults. For anything beyond
Minikube, move them into Kubernetes `Secret`s.

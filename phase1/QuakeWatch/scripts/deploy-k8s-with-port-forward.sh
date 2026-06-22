#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "Using Docker Desktop Kubernetes..."
kubectl config use-context docker-desktop

echo "Applying Kubernetes manifests..."
kubectl apply -f "$APP_DIR/k8s"

echo "Waiting for deployment rollout..."
kubectl rollout status deployment/quakewatch-deployment -n quakewatch --timeout=180s

echo "Starting automatic port-forward..."
"$APP_DIR/scripts/start-port-forward.sh"

echo ""
echo "Deployment completed."
echo "Open the application here:"
echo "http://localhost:5002"

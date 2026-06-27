#!/bin/bash
set -e

NAMESPACE="quakewatch"
SERVICE_NAME="quakewatch-service"
LOCAL_PORT="5002"
SERVICE_PORT="5000"
PID_FILE="/tmp/quakewatch-port-forward.pid"
LOG_FILE="/tmp/quakewatch-port-forward.log"

echo "Using Kubernetes context: docker-desktop"
kubectl config use-context docker-desktop >/dev/null

echo "Checking Kubernetes namespace..."
kubectl get namespace "$NAMESPACE" >/dev/null

echo "Stopping old port-forward process if exists..."
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" >/dev/null 2>&1; then
    kill "$OLD_PID" >/dev/null 2>&1 || true
  fi
  rm -f "$PID_FILE"
fi

echo "Starting port-forward in the background..."
nohup kubectl port-forward service/"$SERVICE_NAME" "$LOCAL_PORT":"$SERVICE_PORT" -n "$NAMESPACE" > "$LOG_FILE" 2>&1 &

PF_PID=$!
echo "$PF_PID" > "$PID_FILE"

sleep 3

if kill -0 "$PF_PID" >/dev/null 2>&1; then
  echo "Port-forward is running."
  echo "PID: $PF_PID"
  echo "URL: http://localhost:$LOCAL_PORT"
  echo "Log file: $LOG_FILE"
else
  echo "Port-forward failed. Log:"
  cat "$LOG_FILE"
  exit 1
fi

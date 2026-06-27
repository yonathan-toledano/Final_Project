#!/bin/bash
set -e

PID_FILE="/tmp/quakewatch-port-forward.pid"

if [ -f "$PID_FILE" ]; then
  PF_PID=$(cat "$PID_FILE")
  if kill -0 "$PF_PID" >/dev/null 2>&1; then
    kill "$PF_PID"
    echo "Stopped port-forward process with PID: $PF_PID"
  else
    echo "No running port-forward process found."
  fi
  rm -f "$PID_FILE"
else
  echo "No PID file found. Nothing to stop."
fi

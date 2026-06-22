#!/bin/bash
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VALUES_FILE="$APP_DIR/charts/quakewatch/values.yaml"

cd "$APP_DIR"

python3 <<'PY'
from pathlib import Path

path = Path("charts/quakewatch/values.yaml")
text = path.read_text()

if "appName: QuakeWatch GitOps Demo" in text:
    text = text.replace("appName: QuakeWatch GitOps Demo", "appName: QuakeWatch")
else:
    text = text.replace("appName: QuakeWatch", "appName: QuakeWatch GitOps Demo")

path.write_text(text)
PY

echo "Chart value changed:"
grep -n "appName:" "$VALUES_FILE"

git add charts/quakewatch/values.yaml
git commit -m "Demo GitOps chart value change"
git push

echo ""
echo "After the change is merged to main, ArgoCD should detect the chart change and sync it."

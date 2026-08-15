FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY __init__.py /app/__init__.py
COPY monitor.py /app/monitor.py

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, json; print(json.load(urllib.request.urlopen('http://127.0.0.1/health'))['ok'])" || exit 1

CMD ["uvicorn", "monitor:app", "--host", "0.0.0.0", "--port", "80"]

# RedWar — Containerized Web Platform and Game Server
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install build dependencies for native compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose HTTP REST / Web client port and WebSocket server port
EXPOSE 8000
EXPOSE 8765

CMD ["python", "launcher.py", "web", "--host", "0.0.0.0", "--port", "8000"]

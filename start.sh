#!/bin/bash
set -e

# Export the dynamic application port (provided by Render or default 8000)
export PORT=${PORT:-8000}
export APP_PORT=${PORT}
export BRIDGE_PORT=3000
export WAHA_BASE_URL=http://127.0.0.1:3000

echo "=========================================="
echo "Starting Gerry's dnata WhatsApp Bot Cloud"
echo "Public Port: ${PORT}"
echo "Bridge Port: ${BRIDGE_PORT}"
echo "=========================================="

# 1. Start Node.js Baileys WhatsApp Bridge in background
echo "Starting WhatsApp Baileys Bridge..."
node bridge/server.js &
BRIDGE_PID=$!

# 2. Start Background Outbox Worker
echo "Starting Outbox Worker..."
python -m app.worker.outbox_worker &
WORKER_PID=$!

# Trap signals for graceful shutdown
trap "kill -TERM $BRIDGE_PID $WORKER_PID 2>/dev/null" SIGTERM SIGINT

# 3. Start FastAPI Webhook & Calculation Server in foreground
echo "Starting FastAPI Server on port ${PORT}..."
uvicorn app.api.app:app --host 0.0.0.0 --port ${PORT}

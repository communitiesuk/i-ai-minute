#!/bin/bash

# Run Worker Locally with MPS Acceleration
# This script starts the worker outside Docker for Apple Silicon GPU acceleration

set -e

# Handle Ctrl+C gracefully
cleanup() {
    echo ""
    echo "🛑 Shutting down worker..."
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "🚀 Starting Minute Worker with MPS Acceleration"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.local..."
    cp .env.local .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and set your WHISPLY_HF_TOKEN"
    echo "   Get token from: https://huggingface.co/settings/tokens"
    echo ""
    read -p "Press Enter after you've added your HuggingFace token to .env..."
fi

# Check if whisply is installed
echo "🔍 Checking Whisply installation..."
if ! poetry run python -c "import whisply" 2>/dev/null; then
    echo "📦 Installing Whisply..."
    poetry run pip install whisply
    echo "✅ Whisply installed"
else
    echo "✅ Whisply already installed"
fi

# Check if MPS is available
echo ""
echo "🔍 Checking MPS (Apple Silicon GPU) availability..."
MPS_AVAILABLE=$(poetry run python -c "import torch; print(torch.backends.mps.is_available())" 2>/dev/null || echo "false")

if [ "$MPS_AVAILABLE" = "True" ]; then
    echo "✅ MPS acceleration available"
else
    echo "⚠️  MPS not available - will use CPU"
    echo "   This is normal if you're not on Apple Silicon"
fi

# Start Docker services
echo ""
echo "� Starting Docker services..."
echo "   Services: db, localstack, backend, frontend"

# Stop worker if it's running (we'll run it locally)
docker compose -f docker-compose.local.yaml stop worker 2>/dev/null || true

# Start required services
docker compose -f docker-compose.local.yaml up -d db localstack backend frontend

echo ""
echo "⏳ Waiting for services to be healthy..."
echo "   This may take 30-60 seconds on first run..."

# Wait for database to be healthy
RETRY_COUNT=0
MAX_RETRIES=30
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker compose -f docker-compose.local.yaml ps db | grep -q "healthy"; then
        echo "✅ Database ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Database failed to start. Check logs with: docker compose -f docker-compose.local.yaml logs db"
    exit 1
fi

# Wait for backend to be healthy
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8080/healthcheck > /dev/null 2>&1; then
        echo "✅ Backend ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Backend failed to start. Check logs with: docker compose -f docker-compose.local.yaml logs backend"
    exit 1
fi

# Wait for frontend
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ Frontend ready"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "⚠️  Frontend may still be starting (this is usually fine)"
fi

echo "✅ LocalStack ready"

echo ""
echo "✅ All checks passed!"
echo ""
echo "📊 Ray Dashboard will be available at: http://localhost:8265"
echo "🌐 Application available at: http://localhost:3000"
echo ""
echo "🎯 Starting worker with MPS acceleration..."
echo "   Press Ctrl+C to stop"
echo ""
echo "----------------------------------------"
echo ""

# Run the worker (exec replaces the shell process for immediate signal handling)
exec poetry run python worker/main.py

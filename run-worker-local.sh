#!/bin/bash

# Run Worker Locally with MPS Acceleration
# This script starts the worker outside Docker for Apple Silicon GPU acceleration

set -e

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

# Check if Docker services are running
echo ""
echo "🔍 Checking Docker services..."
if ! docker compose -f docker-compose.local.yaml ps | grep -q "db.*Up"; then
    echo "⚠️  Docker services not running"
    echo "   Starting required services (db, localstack, backend, frontend)..."
    docker compose -f docker-compose.local.yaml up -d db localstack backend frontend
    echo "⏳ Waiting for services to be ready..."
    sleep 5
else
    echo "✅ Docker services running"
fi

# Stop Docker worker if running
if docker compose -f docker-compose.local.yaml ps | grep -q "worker.*Up"; then
    echo "🛑 Stopping Docker worker container..."
    docker compose -f docker-compose.local.yaml stop worker
fi

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

# Run the worker
poetry run python worker/main.py

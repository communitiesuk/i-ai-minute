#!/bin/bash

# Run Worker Locally with MPS Acceleration
# This script starts the worker outside Docker for Apple Silicon GPU acceleration

set -e

# Handle Ctrl+C gracefully
cleanup() {
    echo ""
    echo "🛑 Shutting down worker..."
    if [ ! -z "$OLLAMA_PID" ]; then
        echo "🛑 Stopping Ollama service..."
        kill $OLLAMA_PID 2>/dev/null || true
    fi
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

# Check for native Ollama installation (required for MPS acceleration)
echo ""
echo "🤖 Checking Ollama installation..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found. Please install it for MPS acceleration:"
    echo "   brew install ollama"
    echo ""
    echo "   Or download from: https://ollama.ai/download"
    exit 1
fi
echo "✅ Ollama installed"

# Start Ollama service if not already running
echo "🚀 Starting Ollama service..."
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo "✅ Ollama service started (PID: $OLLAMA_PID)"
    sleep 3
else
    echo "✅ Ollama service already running"
fi

# Verify Ollama is responding
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama service not responding. Check logs at /tmp/ollama.log"
    exit 1
fi

# Check if required models are available
FAST_MODEL=$(grep "FAST_LLM_MODEL_NAME" .env 2>/dev/null | cut -d'=' -f2 || echo "llama3.1:8b-instruct-q4_K_M")
BEST_MODEL=$(grep "BEST_LLM_MODEL_NAME" .env 2>/dev/null | cut -d'=' -f2 || echo "llama3.1:8b-instruct-q4_K_M")

for MODEL in "$FAST_MODEL" "$BEST_MODEL"; do
    if [ -n "$MODEL" ] && ! ollama list | grep -q "$MODEL"; then
        echo ""
        echo "❌ Model '$MODEL' not found!"
        echo ""
        echo "📥 Please download: ollama pull $MODEL"
        echo ""
        echo "💡 Recommended: llama3.1:8b-instruct-q4_K_M (~4.9GB)"
        echo ""
        exit 1
    fi
done
echo "✅ Required models available"

# Start Docker services
echo ""
echo "🐳 Starting Docker services..."
echo "   Services: db, localstack, backend, frontend"

# Stop worker if it's running (we'll run it locally)
docker compose -f docker-compose.local.yaml stop worker 2>/dev/null || true

# Start required services (Ollama runs natively for MPS acceleration)
docker compose -f docker-compose.local.yaml up -d db localstack backend frontend

# Function to wait for service health
wait_for_service() {
    local service_name=$1
    local check_command=$2
    local max_retries=30
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if eval "$check_command" > /dev/null 2>&1; then
            echo "✅ $service_name ready"
            return 0
        fi
        retry_count=$((retry_count + 1))
        sleep 2
    done
    
    return 1
}

echo ""
echo "⏳ Waiting for services to be healthy..."
echo "   This may take 30-60 seconds on first run..."

# Wait for services
wait_for_service "Database" "docker compose -f docker-compose.local.yaml ps db | grep -q 'healthy'" || {
    echo "❌ Database failed to start. Check logs: docker compose -f docker-compose.local.yaml logs db"
    exit 1
}

wait_for_service "Backend" "curl -s http://localhost:8080/healthcheck" || {
    echo "❌ Backend failed to start. Check logs: docker compose -f docker-compose.local.yaml logs backend"
    exit 1
}

wait_for_service "Frontend" "curl -s http://localhost:3000" || echo "⚠️  Frontend may still be starting"
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

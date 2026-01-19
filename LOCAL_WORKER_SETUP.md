# Running Worker Locally with MPS Acceleration

This guide shows how to run the worker locally on your Mac with Apple Silicon MPS acceleration for faster Whisply transcription, while keeping other services in Docker.

## Why Run Worker Locally?

- **MPS Acceleration**: Docker containers can't access your Mac's GPU. Running locally enables Metal Performance Shaders for 3-5x faster transcription
- **Better Performance**: Direct access to system resources
- **Easier Debugging**: See logs directly in your terminal

## Prerequisites

1. **Apple Silicon Mac** (M1, M2, M3, M4, or M5)
2. **Python 3.12** installed
3. **Poetry** installed
4. **HuggingFace Token** for speaker diarization

## Setup Steps

### 1. Install Dependencies

```bash
# Navigate to project directory
cd /Users/patkuc/MHCLG/i-ai-minute

# Install project dependencies with worker group
poetry install --with worker

# Install Whisply (not in Poetry dependencies since it's Docker-specific)
poetry run pip install whisply
```

### 2. Configure Environment

```bash
# Copy the local environment template
cp .env.local .env

# Edit .env and set:
# - WHISPLY_DEVICE=mps (for Apple Silicon GPU)
# - WHISPLY_HF_TOKEN=hf_your_actual_token_here
# - Keep other settings as-is
```

**Important `.env` settings for local worker:**

```bash
# Database (connect to Docker container)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Queue service (connect to Docker LocalStack)
LOCALSTACK_URL=http://localhost:4566
QUEUE_SERVICE_NAME=sqs

# Storage (connect to Docker backend)
STORAGE_SERVICE_NAME=local
LOCAL_STORAGE_PATH=./.data

# Whisply with MPS
WHISPLY_DEVICE=mps
WHISPLY_MODEL=large-v3-turbo
WHISPLY_ENABLE_DIARIZATION=true
WHISPLY_HF_TOKEN=hf_your_actual_token_here

# LM Studio
LMSTUDIO_BASE_URL=http://localhost:1234
FAST_LLM_MODEL_NAME=qwen/qwen3-4b
BEST_LLM_MODEL_NAME=qwen/qwen3-8b
```

### 3. Start Docker Services (Without Worker)

Create a modified docker-compose file or stop the worker:

```bash
# Start all services
docker compose -f docker-compose.local.yaml up -d

# Stop the worker container
docker compose -f docker-compose.local.yaml stop worker
```

Or use this command to start only the required services:

```bash
docker compose -f docker-compose.local.yaml up -d db localstack backend frontend
```

### 4. Run Worker Locally

```bash
# Make sure you're in the project directory
cd /Users/patkuc/MHCLG/i-ai-minute

# Run the worker
poetry run python -m worker.worker_service
```

You should see output like:
```
Starting queue service...
2026-01-15 14:44:00 - common.services.transcription_services.transcription_manager - INFO - registered transcription service whisply_local
Ray dashboard available at http://127.0.0.1:8265
```

### 5. Verify MPS is Working

When you upload an audio file for transcription, check the worker logs for:

```
Running Whisply transcription: whisply run --files ... --device mps ...
```

You should see significantly faster transcription times compared to CPU.

## Performance Comparison

Typical transcription times for a 2-minute audio file:

- **CPU**: ~60-90 seconds
- **MPS (Apple Silicon)**: ~15-25 seconds
- **Speed improvement**: 3-4x faster

## Troubleshooting

### Worker Can't Connect to Database

**Error**: `Connection refused` to PostgreSQL

**Solution**: Ensure the database port is exposed in docker-compose:
```yaml
db:
  ports:
    - "5432:5432"
```

### Worker Can't Connect to LocalStack

**Error**: `Connection refused` to LocalStack

**Solution**: Ensure LocalStack port is exposed:
```yaml
localstack:
  ports:
    - "4566:4566"
```

### MPS Not Available

**Error**: `MPS device not found`

**Solution**: 
1. Verify you have Apple Silicon: `sysctl -n machdep.cpu.brand_string`
2. Check PyTorch MPS support:
   ```bash
   poetry run python -c "import torch; print('MPS available:', torch.backends.mps.is_available())"
   ```
3. If not available, fall back to CPU: `WHISPLY_DEVICE=cpu`

### Whisply Not Found

**Error**: `ModuleNotFoundError: No module named 'whisply'`

**Solution**:
```bash
poetry run pip install whisply
```

### HuggingFace Token Issues

**Error**: `Failed to download pyannote models`

**Solution**:
1. Verify your token: https://huggingface.co/settings/tokens
2. Accept model terms:
   - https://huggingface.co/pyannote/segmentation-3.0
   - https://huggingface.co/pyannote/speaker-diarization-3.1
3. Update `.env` with correct token

## Stopping Services

```bash
# Stop the local worker
# Press Ctrl+C in the terminal running the worker

# Stop Docker services
docker compose -f docker-compose.local.yaml down
```

## Development Workflow

1. **Start Docker services** (database, backend, frontend, localstack)
2. **Start LM Studio** with your models loaded
3. **Run worker locally** with MPS acceleration
4. **Access application** at http://localhost:3000
5. **Monitor worker** logs in your terminal
6. **View Ray dashboard** at http://localhost:8265

## Benefits of This Setup

✅ **Fast transcription** with MPS GPU acceleration  
✅ **Easy debugging** - see worker logs directly  
✅ **Hot reload** - code changes take effect immediately  
✅ **Resource efficient** - only run what you need in Docker  
✅ **Best of both worlds** - containerized services + native performance  

## Switching Back to Full Docker

If you want to run everything in Docker again:

```bash
# Stop local worker (Ctrl+C)

# Start all services including worker
docker compose -f docker-compose.local.yaml up -d

# Note: Worker will use CPU, not MPS
```

## Next Steps

- Monitor transcription performance in Ray dashboard: http://localhost:8265
- Check worker logs for any errors
- Test with different audio files
- Experiment with different Whisper models (small, medium, large-v3-turbo)

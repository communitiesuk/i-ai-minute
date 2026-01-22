# Local Setup Guide

Run Minute locally with hardware-accelerated transcription and local Ollama LLM.

## Prerequisites

**System Requirements:**
- Docker Desktop (required for any local setup)
- Python 3.12 (required for any local setup)
- Poetry (required for any local setup)
- FFmpeg
- Ollama

**macOS Installation:**
```bash
brew install ffmpeg ollama poetry
```

**Required:**
1. **HuggingFace Token**: https://huggingface.co/settings/tokens (starts with `hf_`)
   - Accept terms at: https://huggingface.co/pyannote/segmentation-3.0
   - Accept terms at: https://huggingface.co/pyannote/speaker-diarization-3.1
2. **Ollama Model**: Download quantized model (~4.9GB)
   ```bash
   ollama pull llama3.1:8b-instruct-q4_K_M
   ```

## Quick Start

```bash
# Install dependencies
poetry install --with worker

# Download Ollama model
ollama pull llama3.1:8b-instruct-q4_K_M

# Configure environment
cp .env.local .env
# Edit .env and add: WHISPLY_HF_TOKEN=hf_your_token

# Run everything
./run-worker-local.sh
```

Access the app at http://localhost:3000

## What `run-worker-local.sh` Does

1. Starts Docker services (database, backend, frontend, localstack)
2. Waits for services to be healthy
3. Runs the worker locally with MPS (Apple Silicon GPU) acceleration
4. Enables 3-4x faster transcription vs CPU

## Architecture

- **Docker**: Database, backend, frontend, localstack
- **Local Worker**: Runs natively for GPU access (MPS on Apple Silicon)
- **Transcription**: Whisply with hardware acceleration
- **LLM**: Ollama (local, runs natively for MPS acceleration)

## LLM Configuration

**Model Selection:**
- Default: `llama3.1:8b-instruct-q4_K_M` (4.9GB, recommended)
- Configure in `.env`: `FAST_LLM_MODEL_NAME` and `BEST_LLM_MODEL_NAME`

**Structured Outputs:**
- Uses JSON mode + Pydantic validation (not OpenAI's `.parse()`)
- JSON schema automatically injected into prompts
- All requests/responses logged at DEBUG level

## Monitoring

- **Application**: http://localhost:3000
- **Ray Dashboard**: http://localhost:8265
- **Worker Logs**: Terminal output from `run-worker-local.sh`

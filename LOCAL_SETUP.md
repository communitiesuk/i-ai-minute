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
2. **Ollama Model**: Download a quantized LLama3.2 3b model
   ```bash
   ollama pull llama3.2:3b-instruct-q4_K_M
   ```

## Quick Start

```bash
# Install dependencies
poetry install --with worker,local-dev

# Download Ollama model
ollama pull llama3.2:3b-instruct-q4_K_M

# Configure environment
cp .env.local .env
```
Before moving on to the next step, edit the .env file and add: WHISPLY_HF_TOKEN=hf_your_token
```bash
# Run worker locally
./run-worker-local.sh
```

Access the app at http://localhost:3000

## Architecture

- **Docker**: Database, backend, frontend, localstack
- **Local Worker**: Runs natively for GPU access (MPS on Apple Silicon)
- **Transcription**: Whisply with hardware acceleration
- **LLM**: Ollama (local, runs natively for MPS acceleration)

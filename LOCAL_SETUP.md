# Local Setup Guide

Run Minute locally with hardware-accelerated transcription and OpenAI LLM services.

## Prerequisites

**System Requirements:**
- Docker Desktop
- Python 3.12
- Poetry
- FFmpeg

**macOS Installation:**
```bash
brew install ffmpeg
curl -sSL https://install.python-poetry.org | python3 -
```

**API Keys Required:**
1. **OpenAI API Key**: https://platform.openai.com/api-keys (starts with `sk-`)
2. **HuggingFace Token**: https://huggingface.co/settings/tokens (starts with `hf_`)
   - Accept terms at: https://huggingface.co/pyannote/segmentation-3.0
   - Accept terms at: https://huggingface.co/pyannote/speaker-diarization-3.1

## Quick Start

```bash
# Install dependencies
poetry install --with worker

# Install Whisply
poetry run pip install whisply

# Configure environment
cp .env.local .env
# Edit .env and add your API keys:
# - OPENAI_DIRECT_API_KEY=sk_your_key
# - WHISPLY_HF_TOKEN=hf_your_token

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
- **LLM**: OpenAI API (gpt-4o-mini for fast, gpt-4o for best)

## Monitoring

- **Application**: http://localhost:3000
- **Ray Dashboard**: http://localhost:8265
- **Worker Logs**: Terminal output from `run-worker-local.sh`

## Troubleshooting

**Worker won't start:**
```bash
# Check if ports are available
lsof -i :5432  # PostgreSQL
lsof -i :4566  # LocalStack
lsof -i :8080  # Backend
```

**Transcription fails:**
- Verify HuggingFace token in `.env`
- Check you accepted model terms (see API Keys section)
- Ensure FFmpeg is installed: `ffmpeg -version`

**MPS not available:**
```bash
# Check MPS support
poetry run python -c "import torch; print('MPS:', torch.backends.mps.is_available())"

# Fall back to CPU if needed (edit .env):
WHISPLY_DEVICE=cpu
```

**Stop everything:**
```bash
# Ctrl+C to stop worker
# Then stop Docker services:
docker compose -f docker-compose.local.yaml down
```

## Performance

Typical transcription times for 2-minute audio:
- **CPU**: 60-90 seconds
- **MPS (Apple Silicon)**: 15-25 seconds

## Development Tips

- Worker logs show detailed transcription progress
- Output files saved in `.whisply_temp/` for debugging
- Code changes to worker require restart (Ctrl+C, then re-run script)
- Frontend/backend changes hot-reload automatically

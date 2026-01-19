# Local Setup Guide - Minute Application

Complete step-by-step guide to run Minute locally with Whisply transcription and LM Studio.

---

## Step 1: Install System Prerequisites

### Install Docker Desktop
1. Download Docker Desktop from https://www.docker.com/products/docker-desktop
2. Install and start Docker Desktop
3. Verify installation:
   ```bash
   docker --version
   docker compose version
   ```

### Install FFmpeg
```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install ffmpeg

# Windows
winget install Gyan.FFmpeg
```

Verify:
```bash
ffmpeg -version
```

### Install Poetry
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add Poetry to your PATH (follow the installer instructions), then verify:
```bash
poetry --version
```

---

## Step 2: Install LM Studio

1. **Download LM Studio**
   - Visit https://lmstudio.ai/
   - Download for your operating system
   - Install the application

2. **Download a Model**
   - Open LM Studio
   - Go to the "Discover" tab
   - Search for and download one of these models:
     - **Mistral 7B Instruct v0.3** (recommended - good balance)
     - **Llama 3.1 8B Instruct** (excellent for structured outputs)
     - **Phi-3 Medium** (smaller, faster)

3. **Start the Server**
   - Go to the "Local Server" tab
   - Select your downloaded model
   - Click "Start Server"
   - Verify it shows "Server running on port 1234"
   - **Important**: In server settings, enable:
     - ✅ Enable CORS
     - ✅ JSON mode (if available)

4. **Test the Server**
   ```bash
   curl http://localhost:1234/v1/models
   ```
   You should see JSON output with your model listed.

---

## Step 3: Get HuggingFace Token

Speaker diarization requires a HuggingFace token:

1. **Create Account**
   - Go to https://huggingface.co/join
   - Sign up (free)

2. **Create Access Token**
   - Go to https://huggingface.co/settings/tokens
   - Click "New token"
   - Name it "minute-local"
   - Select "Read" access
   - Click "Generate"
   - **Copy the token** (starts with `hf_`)

3. **Accept Model Terms**
   - Visit https://huggingface.co/pyannote/segmentation-3.0
   - Click "Agree and access repository"
   - Visit https://huggingface.co/pyannote/speaker-diarization-3.1
   - Click "Agree and access repository"

---

## Step 4: Clone and Configure the Project

1. **Navigate to Project Directory**
   ```bash
   cd /Users/patkuc/MHCLG/i-ai-minute
   ```

2. **Install Project Dependencies**
   ```bash
   poetry install --with worker --extras local
   ```
   This installs all dependencies including Whisply.

3. **Create Environment File**
   ```bash
   cp .env.local .env
   ```

4. **Edit the `.env` File**
   Open `.env` in your editor and update:
   ```bash
   # REQUIRED: Add your HuggingFace token
   WHISPLY_HF_TOKEN=hf_your_actual_token_here
   
   # Optional: Adjust these based on your hardware
   WHISPLY_DEVICE=auto          # Options: auto, cpu, gpu, mps, mlx
   WHISPLY_MODEL=large-v3-turbo # Or: small, medium, large-v3
   
   # LM Studio settings
   LMSTUDIO_BASE_URL=http://host.docker.internal:1234
   ```

   **Device Selection Guide:**
   - `auto` - Let Whisply choose (recommended)
   - `cpu` - Use CPU only (slower but works everywhere)
   - `gpu` - NVIDIA GPU with CUDA
   - `mps` - Apple Silicon (M1-M5) legacy mode
   - `mlx` - Apple Silicon (M1-M5) optimized mode

   **Model Selection Guide:**
   - `tiny` - Fastest, lowest quality (~1GB RAM)
   - `small` - Fast, decent quality (~2GB RAM)
   - `medium` - Good balance (~5GB RAM)
   - `large-v3-turbo` - Best balance ⭐ **Recommended** (~10GB RAM)
   - `large-v3` - Highest quality (~10GB RAM)

---

## Step 5: Start the Application

1. **Ensure LM Studio is Running**
   - Check that LM Studio server shows "Running on port 1234"

2. **Build and Start All Services**
   ```bash
   docker compose -f docker-compose.local.yaml up --build
   ```

   This will:
   - Build the Docker containers (first time takes 5-10 minutes)
   - Start the database
   - Start the backend API
   - Start the worker (with Whisply)
   - Start the frontend
   - Start LocalStack (AWS emulation)

3. **Wait for Services to Start**
   Look for these messages:
   ```
   ✓ Database ready
   ✓ Backend started on port 8080
   ✓ Worker ready
   ✓ Frontend started on port 3000
   ```

4. **Access the Application**
   - **Web Interface**: http://localhost:3000
   - **API Documentation**: http://localhost:8080/docs
   - **Ray Dashboard** (worker monitoring): http://localhost:8265

---

## Step 6: Test the Application

1. **Open Web Interface**
   - Navigate to http://localhost:3000

2. **Upload an Audio File**
   - Click "Upload" or drag and drop an audio file
   - Supported formats: MP3, WAV, M4A, MP4, etc.

3. **Select a Template**
   - Choose a meeting template (e.g., "General Meeting")

4. **Start Transcription**
   - Click "Start Transcription"
   - Monitor progress in the UI

5. **View Results**
   - Transcription will show speaker labels (SPEAKER_00, SPEAKER_01, etc.)
   - Minutes will be generated automatically
   - You can edit and export the results

---

## Monitoring and Logs

### View Logs
```bash
# All services
docker compose -f docker-compose.local.yaml logs -f

# Specific service
docker compose -f docker-compose.local.yaml logs -f worker
docker compose -f docker-compose.local.yaml logs -f backend
```

### Monitor Worker
- Open http://localhost:8265 for Ray Dashboard
- Shows active jobs, resource usage, and worker status

### Check Service Health
```bash
# Backend health
curl http://localhost:8080/healthcheck

# Check running containers
docker compose -f docker-compose.local.yaml ps
```

---

## Stopping the Application

```bash
# Stop all services (keeps data)
docker compose -f docker-compose.local.yaml down

# Stop and remove all data (fresh start)
docker compose -f docker-compose.local.yaml down -v
```

---

## Troubleshooting

### LM Studio Connection Issues

**Problem**: "Connection refused" or "Cannot connect to LM Studio"

**Solutions**:
1. Verify LM Studio server is running on port 1234
2. Check CORS is enabled in LM Studio settings
3. On Linux, you may need to use `http://172.17.0.1:1234` instead of `host.docker.internal`
   - Update `LMSTUDIO_BASE_URL` in `.env`

**Test connection from inside Docker**:
```bash
docker compose -f docker-compose.local.yaml exec worker curl http://host.docker.internal:1234/v1/models
```

### Whisply Issues

**Problem**: "whisply: command not found" in worker logs

**Solutions**:
1. Rebuild the worker container:
   ```bash
   docker compose -f docker-compose.local.yaml build --no-cache worker
   docker compose -f docker-compose.local.yaml up worker
   ```

**Problem**: Speaker diarization fails

**Solutions**:
1. Verify `WHISPLY_HF_TOKEN` is set correctly in `.env`
2. Check you accepted terms for both pyannote models
3. Check worker logs for specific error:
   ```bash
   docker compose -f docker-compose.local.yaml logs worker | grep -i error
   ```

**Problem**: GPU not detected

**Solutions**:
- For NVIDIA GPU on Linux:
  ```bash
  # Install nvidia-docker2
  sudo apt-get install nvidia-docker2
  sudo systemctl restart docker
  
  # Update docker-compose.local.yaml to add GPU support
  ```
- For Apple Silicon, use `WHISPLY_DEVICE=mlx` in `.env`

### Performance Issues

**Slow transcription**:
1. Use smaller model: `WHISPLY_MODEL=small` in `.env`
2. Disable diarization: `WHISPLY_ENABLE_DIARIZATION=false`
3. Use GPU if available: `WHISPLY_DEVICE=gpu` or `mlx`

**Slow minute generation**:
1. Use smaller LLM in LM Studio (Mistral 7B instead of 70B)
2. Reduce max tokens: `LMSTUDIO_MAX_TOKENS=2048` in `.env`
3. Enable GPU acceleration in LM Studio settings

**Out of memory**:
1. Use smaller Whisper model: `WHISPLY_MODEL=small`
2. Use smaller LLM in LM Studio
3. Increase Docker memory limit in Docker Desktop settings

### Database Issues

**Problem**: Database connection errors

**Solution**:
```bash
# Reset database
docker compose -f docker-compose.local.yaml down -v
docker compose -f docker-compose.local.yaml up -d db
# Wait for database to be ready, then start other services
docker compose -f docker-compose.local.yaml up
```

### Port Conflicts

**Problem**: "Port already in use"

**Solutions**:
1. Check what's using the port:
   ```bash
   # macOS/Linux
   lsof -i :3000  # or :8080, :5432, etc.
   
   # Windows
   netstat -ano | findstr :3000
   ```
2. Stop the conflicting service or change ports in `docker-compose.local.yaml`

---

## Development Mode

For active development with automatic reload:

```bash
docker compose -f docker-compose.local.yaml up --watch
```

This enables:
- File watching for code changes
- Automatic container restarts
- Hot reload for frontend

---

## Data Storage

All data is stored locally:

- **Audio files**: `./.data/` directory in project root
- **Database**: Docker volume `local_postgres_data`
- **Transcriptions**: PostgreSQL database
- **Models**: 
  - Whisper models: `~/.cache/whisper/`
  - pyannote models: `~/.cache/huggingface/`
  - LM Studio models: `~/.cache/lm-studio/`

---

---

## Alternative: Run Worker Locally with MPS Acceleration (Apple Silicon)

For **significantly faster transcription** on Apple Silicon Macs (M1-M5), you can run the worker locally with GPU acceleration while keeping other services in Docker.

### Why Run Worker Locally?

- **3-4x faster transcription** using Metal Performance Shaders (MPS)
- **Direct GPU access** - Docker containers can't use your Mac's GPU
- **Easier debugging** - see logs directly in your terminal
- **Hot reload** - code changes take effect immediately

### Quick Setup

**Option 1: Use the automated script**

```bash
# This script handles everything automatically
./run-worker-local.sh
```

**Option 2: Manual setup**

```bash
# 1. Install Whisply locally
poetry install --with worker
poetry run pip install whisply

# 2. Configure environment
cp .env.local .env
# Edit .env and add your WHISPLY_HF_TOKEN

# 3. Start Docker services (without worker)
docker compose -f docker-compose.local.yaml up -d db localstack backend frontend

# 4. Run worker locally
poetry run python -m worker.worker_service
```

### Configuration for Local Worker

Your `.env` file should have these settings:

```bash
# Connect to Docker services on localhost
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
LOCALSTACK_URL=http://localhost:4566

# Enable MPS acceleration
WHISPLY_DEVICE=mps
WHISPLY_MODEL=large-v3-turbo
WHISPLY_ENABLE_DIARIZATION=true
WHISPLY_HF_TOKEN=hf_your_actual_token_here

# LM Studio (already on localhost)
LMSTUDIO_BASE_URL=http://localhost:1234
FAST_LLM_MODEL_NAME=qwen/qwen3-4b
BEST_LLM_MODEL_NAME=qwen/qwen3-8b
```

### Performance Comparison

Typical transcription times for a 2-minute audio file:

| Device | Time | Speed |
|--------|------|-------|
| CPU (Docker) | 60-90 seconds | 1x |
| MPS (Local) | 15-25 seconds | **3-4x faster** ⚡ |

### Monitoring

- **Ray Dashboard**: http://localhost:8265
- **Application**: http://localhost:3000
- **Worker logs**: Visible directly in your terminal

### Switching Between Docker and Local Worker

**To use Docker worker** (slower, CPU only):
```bash
# Stop local worker (Ctrl+C)
docker compose -f docker-compose.local.yaml up -d worker
```

**To use local worker** (faster, MPS GPU):
```bash
docker compose -f docker-compose.local.yaml stop worker
./run-worker-local.sh
```

### Troubleshooting Local Worker

**Can't connect to database:**
```bash
# Ensure database port is exposed
docker compose -f docker-compose.local.yaml ps
# Should show db with 0.0.0.0:5432->5432/tcp
```

**MPS not available:**
```bash
# Check MPS support
poetry run python -c "import torch; print('MPS:', torch.backends.mps.is_available())"

# If false, fall back to CPU
# Edit .env: WHISPLY_DEVICE=cpu
```

**For detailed instructions**, see `LOCAL_WORKER_SETUP.md`.

---

## Next Steps

### Customize Templates
- Edit meeting templates in `backend/templates/`
- Restart backend to apply changes

### Adjust Prompts
- Modify LLM prompts in `common/prompts.py`
- Restart worker to apply changes

### Monitor Performance
- Use Ray Dashboard at http://localhost:8265
- Check resource usage and job status

### Add Custom Models
- Download additional Whisper models (auto-downloaded on first use)
- Download different LLMs in LM Studio

---

## Quick Reference

### Essential Commands
```bash
# Start everything
docker compose -f docker-compose.local.yaml up --build

# Stop everything
docker compose -f docker-compose.local.yaml down

# View logs
docker compose -f docker-compose.local.yaml logs -f worker

# Rebuild specific service
docker compose -f docker-compose.local.yaml build --no-cache worker

# Fresh start (deletes all data)
docker compose -f docker-compose.local.yaml down -v
docker compose -f docker-compose.local.yaml up --build
```

### Important URLs
- **Application**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs
- **Ray Dashboard**: http://localhost:8265
- **Database**: localhost:5432

### Configuration Files
- **Environment**: `.env`
- **Docker Compose**: `docker-compose.local.yaml`
- **Dependencies**: `pyproject.toml`

---

## Getting Help

- **Whisply Issues**: https://github.com/tsmdt/whisply/issues
- **LM Studio Help**: https://lmstudio.ai/discord
- **Docker Help**: https://docs.docker.com/

---

## Privacy & Security

✅ All processing happens on your machine  
✅ No data sent to cloud services  
✅ No API costs  
✅ Complete data control  
✅ Works offline (after initial setup)  

Your HuggingFace token is only used to download speaker diarization models once. After that, everything runs locally.

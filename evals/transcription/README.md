# Transcription Evaluation Suite

Evaluation framework for comparing transcription services.

## System Requirements

### FFmpeg
This project requires FFmpeg for audio processing:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Azure Speech API credentials
```

## Environment Variables

- `AZURE_SPEECH_KEY`: Your Azure Cognitive Services Speech API key
- `AZURE_SPEECH_REGION`: Your Azure region (e.g., `uksouth`, `eastus`)

## Usage

Run the evaluation:
```bash
# Evaluate on 10 full meetings
poetry run python src/evaluate.py --num-samples 10

# Quick test: evaluate on 10% of first meeting duration (~9 minutes)
poetry run python src/evaluate.py --num-samples 0.1

# Cache dataset only without running transcription
poetry run python src/evaluate.py --prepare-only
```

Results are saved to `results/evaluation_results_YYYYMMDD_HHMMSS.json` with timestamped filenames to prevent overwriting.

## Configuration

**Sample Selection**:
- `--num-samples N` where N ≥ 1: Evaluate N complete meetings from AMI dataset
- `--num-samples 0.X`: Fractional mode - evaluate X% of first meeting duration (e.g., `0.1` = 10% ≈ 9 minutes)
- `--prepare-only`: Download and cache dataset without running transcription

**Dataset**: Uses AMI Corpus meeting recordings. Audio is automatically:
- Mixed chronologically with overlapping speech preserved
- Converted to mono 16kHz PCM WAV
- Cached in `cache/processed/` for reuse

**Adapters**: Modify `src/evaluate.py` to change:
- Whisper model size (currently `large-v3`)
- Azure language settings (currently `en-US`)
- Add/remove transcription engines

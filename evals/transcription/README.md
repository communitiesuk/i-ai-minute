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
# Evaluate all available meetings
poetry run python src/evaluate.py

# Evaluate 10 full meetings
poetry run python src/evaluate.py --num-samples 10

# Evaluate 10 meetings, using only first 10% of each meeting
poetry run python src/evaluate.py --num-samples 10 --sample-duration-fraction 0.1

# Evaluate 5 meetings, using first 25% of each
poetry run python src/evaluate.py --num-samples 5 --sample-duration-fraction 0.25

# Cache dataset only without running transcription
poetry run python src/evaluate.py --prepare-only
```

Results are saved to `results/evaluation_results_YYYYMMDD_HHMMSS.json` with timestamped filenames to prevent overwriting.

## Configuration

**Sample Selection**:
- `--num-samples N`: Evaluate N meetings from AMI dataset (if not specified, evaluates all available meetings)
- `--sample-duration-fraction 0.X`: Use first X% of each selected meeting (e.g., `0.1` = first 10% of each meeting)
  - Useful for testing multiple meetings with shorter audio clips
- `--prepare-only`: Download and cache dataset without running transcription

**Dataset**: Uses AMI Corpus meeting recordings. Audio is automatically:
- Mixed chronologically with overlapping speech preserved
- Converted to mono 16kHz PCM WAV
- Cached in `cache/processed/` for reuse

**Adapters**: Modify `src/evaluate.py` to change:
- Whisper model size (currently `large-v3`)
- Azure language settings (currently `en-US`)
- Add/remove transcription engines

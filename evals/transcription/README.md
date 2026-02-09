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

This evaluation suite runs from the project root directory and uses the main project's dependencies and `.env` file.

1. Install dependencies (from project root):
```bash
poetry install --with worker,local-dev,evals
```

## Usage

**Run all commands from the project root directory** (`/Users/patkuc/MHCLG/i-ai-minute/`).
This suite relies on the root `.env` and the root Poetry environment.

```bash
# Evaluate all available meetings
poetry run python evals/transcription/src/evaluate.py

# Evaluate 10 full meetings
poetry run python evals/transcription/src/evaluate.py --num-samples 10

# Evaluate 10 meetings, using only first 10% of each meeting
poetry run python evals/transcription/src/evaluate.py --num-samples 10 --sample-duration-fraction 0.1

# Evaluate 5 meetings, using first 25% of each
poetry run python evals/transcription/src/evaluate.py --num-samples 5 --sample-duration-fraction 0.25

# Cache dataset only without running transcription
poetry run python evals/transcription/src/evaluate.py --prepare-only
```

Results are saved to `evals/transcription/results/evaluation_results_YYYYMMDD_HHMMSS.json` with timestamped filenames to prevent overwriting.

### Tests

Run tests from the project root:

```bash
poetry run pytest tests/test_transcription_evals.py
```

## Configuration

**Sample Selection**:
- `--num-samples N`: Evaluate N meetings from AMI dataset (if not specified, evaluates all available meetings)
- `--sample-duration-fraction 0.X`: Use first X% of each selected meeting (e.g., `0.1` = first 10% of each meeting)
  - Useful for testing multiple meetings with shorter audio clips
- `--prepare-only`: Download and cache dataset without running transcription (saved to `evals/transcription/cache/processed/`)

**Dataset**: Uses AMI Corpus meeting recordings. Audio is automatically:
- Mixed chronologically with overlapping speech preserved
- Converted to mono 16kHz PCM WAV
- Cached in `evals/transcription/cache/processed/` for reuse

**Adapters**: Modify `src/evaluate.py` to change:
- Whisper model size (currently `small`)
- Azure language settings (currently `en-GB`)
- Add/remove transcription engines

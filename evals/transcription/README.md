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

### Quick Smoke Test

Fast validation using 2 meetings with 10% of each recording:

```bash
poetry run python evals/transcription/src/evaluate.py \
  --num-samples 2 \
  --sample-duration-fraction 0.1 \
  --max-workers 1
```

### Common Use Cases

```bash
# Prepare dataset (cache audio files without transcription)
poetry run python evals/transcription/src/evaluate.py --prepare-only

# Full evaluation (all meetings, all adapters in parallel)
poetry run python evals/transcription/src/evaluate.py

# Local adapters (Whisper) - use sequential processing
poetry run python evals/transcription/src/evaluate.py \
  --num-samples 10 \
  --max-workers 1

# Evaluate subset with partial recordings
poetry run python evals/transcription/src/evaluate.py \
  --num-samples 5 \
  --sample-duration-fraction 0.25
```

**Important**: When using local transcription adapters (e.g., Whisper), set `--max-workers 1` to avoid resource conflicts and event loop issues.

Results are saved to `evals/transcription/results/evaluation_results_YYYYMMDD_HHMMSS.json` with timestamped filenames to prevent overwriting.

### Tests

Run tests from the project root:

```bash
poetry run pytest tests/test_transcription_evals.py
```

## Configuration

**Command Line Arguments**:
- `--num-samples N`: Evaluate N meetings from AMI dataset (if not specified, evaluates all available meetings)
- `--sample-duration-fraction 0.X`: Use first X% of each selected meeting (e.g., `0.1` = first 10% of each meeting)
  - Useful for testing multiple meetings with shorter audio clips
- `--max-workers N`: Number of parallel workers for transcription (default: 4)
  - Set to `1` when using local transcription adapters (e.g., Whisper) to avoid resource conflicts and event loop issues
  - Higher values work well with API-based adapters (e.g., Azure Speech-to-Text)
- `--prepare-only`: Download and cache dataset without running transcription (saved to `evals/transcription/cache/processed/`)

**Dataset**: Uses AMI Corpus meeting recordings. Audio is automatically:
- Mixed chronologically with overlapping speech preserved
- Converted to mono 16kHz PCM WAV
- Cached in `evals/transcription/cache/processed/` for reuse

**Adapters**: Modify `src/evaluate.py` to change:
- Whisper model size (currently `small`)
- Azure language settings (currently `en-GB`)
- Add/remove transcription engines

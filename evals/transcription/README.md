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
- Azure language settings (currently `en-GB`)
- Add/remove transcription engines

## Output Format

Results are saved as JSON in `results/evaluation_results_YYYYMMDD_HHMMSS.json`.

### Top-Level Structure

```json
{
  "engines": [...]  // Array of engine results
}
```

### Engine-Level Fields

Each engine result contains:

- **`engine`** (string): Engine name (e.g., "Azure Speech-to-Text")
- **`processing_time_ratio`** (float): Real-time factor (processing_time / audio_duration)
- **`word_metrics`** (object): Aggregated word-level counts across all samples
  - `hits` (int): Total correct words
  - `substitutions` (int): Total word substitutions
  - `deletions` (int): Total word deletions
  - `insertions` (int): Total word insertions
  - `speaker_confusions` (int): Total speaker attribution errors
  - `total_words` (int): Total reference words
- **`wer`** (object): Word Error Rate statistics (decimal format, e.g., 0.2218 = 22.18%)
  - `mean`, `min`, `max`, `std` (float)
- **`jaccard_wer`** (object): Jaccard Word Error Rate statistics (decimal format)
  - `mean`, `min`, `max`, `std` (float)
- **`wder`** (object): Word-level Diarization Error Rate statistics (decimal format)
  - `mean`, `min`, `max`, `std` (float)
- **`speaker_count_accuracy`** (object): Speaker identification accuracy
  - `accuracy` (float): Percentage of samples with correct speaker count
  - `total_misses` (int): Number of samples with incorrect speaker count
- **`samples`** (array): Per-sample detailed results

### Sample-Level Fields

Each sample contains:

- **`dataset_index`** (int): Sample identifier
- **`wer`** (object): Word Error Rate metrics
  - `wer` (float): Error rate (decimal)
  - `hits`, `substitutions`, `deletions`, `insertions` (int): Word-level counts
- **`jaccard_wer`** (object): Jaccard Word Error Rate
  - `jaccard_wer` (float): Error rate (decimal)
- **`wder`** (object): Word-level Diarization Error Rate
  - `wder` (float): Error rate (decimal)
  - `speaker_errors` (int): Number of words with wrong speaker attribution
  - `total_words` (int): Total reference words
  - `confusion_count` (int): Number of speakers with attribution errors
- **`speaker_count`** (object): Speaker count metrics
  - `ref_speaker_count` (int): Number of speakers in reference
  - `hyp_speaker_count` (int): Number of speakers in hypothesis
  - `absolute_error` (int): Absolute difference
  - `speaker_count_accuracy` (float): 1.0 if correct, 0.0 if incorrect
- **`debug`** (object): Human-readable debug information
  - `ref_with_speakers` (string): Reference transcript with normalized speaker labels
  - `hyp_with_speakers` (string): Hypothesis transcript with speaker labels

### Metrics

All metrics computed using `jiwer` and `pyannote-metrics`. Aggregated with mean, max, std.

#### Transcription Quality
| Metric | What It Measures |
|--------|------------------|
| **WER** | How accurate is the transcribed text, word by word? |
| **JWER** | How well does the vocabulary match? |

#### Speaker Attribution Quality
| Metric | What It Measures |
|--------|------------------|
| **WDER** | How often are words assigned to the wrong speaker? |

#### Speaker Identification
| Metric | What It Measures |
|--------|------------------|
| **Speaker Count Accuracy** | Did we identify the correct number of speakers? |
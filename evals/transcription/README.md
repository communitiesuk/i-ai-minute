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

**Structure:**
- `adapters[]` - Array of results per transcription engine
  - `name` - Engine identifier
  - `overall_results` - Aggregated metrics across all samples
    - `num_samples` - Sample count
    - `overall_wer_pct` - Overall Word Error Rate (%)
    - `overall_wer_metrics` - Detailed WER breakdown (wer, mer, wil, cer as %, plus counts)
    - `per_sample_wer_min/max/mean/std` - WER statistics (%)
    - `rtf` - Real-time factor (processing_time / audio_duration)
    - `process_sec`, `audio_sec` - Timing totals
    - `diarization` - Speaker metrics (der, jer, miss, false_alarm, confusion as %, speaker_count_error)
  - `entries[]` - Per-sample detailed results
    - `dataset_index` - Sample identifier
    - `results` - Sample metrics (wer_pct, wer_metrics, rtf, diarization)
    - `debug` - Raw data (ref_raw, hyp_raw, diarization segments, engine_debug)

### Metrics

**Transcription:**
- `overall_wer_pct`: Word Error Rate - text accuracy only, doesn't include diarization (mean across samples)
- `per_sample_wer_min/max/mean/std`: WER distribution statistics
- `rtf`: Real-Time Factor - processing speed, <1.0 = faster than real-time (mean across samples)

**Diarization:**
- `der`: Diarization Error Rate - time-based total error = miss + false_alarm + confusion (mean across samples)
  - Standard NIST metric, measures temporal accuracy of speaker segments
  - Can exceed 100% if hypothesis has much more speech time than reference
- `jer`: Jaccard Error Rate - IoU-based per-speaker overlap quality (mean across samples)
  - More stable than DER with overlapping speech
  - Measures speaker boundary alignment independent of timing errors
- `miss`: DER component - reference speech not detected, % of total time (mean)
- `false_alarm`: DER component - detected speech where there's no reference, % of total time (mean)
- `confusion`: DER component - wrong speaker assignment, % of total time (mean)
- `speaker_count_error`: Absolute difference from correct speaker count (mean of |predicted - actual|)

**Per-Sample Data:**
- `entries[].results`: WER, RTF, timing, diarization metrics (DER, JER, miss, false_alarm, confusion, speaker_count_error)
- `entries[].debug`: Full transcripts and diarization segments

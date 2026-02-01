## Usage

1. Download samples (adjust args if needed):
   `poetry run python src/evaluate.py --num-samples 10 --sample-duration-fraction 0.1 --prepare-only`.

2. Transcribe and Evaluate WER:
   `poetry run python -m src.transcriptions_with_sped_audio.evaluate`.

3. Plot:
   `poetry run python -m src.transcriptions_with_sped_audio.plot`.
